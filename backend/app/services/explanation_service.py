import asyncio
import json
import logging
from datetime import datetime, timedelta
import uuid
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.cache import cache
from app.models.all_models import Alert, ThreatExplanation, KnowledgeBase

logger = logging.getLogger("explanation_service")

_embed_model = None

def get_embedding_model():
    """Lazy-loads the SentenceTransformer model for text embeddings."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        # Loads local CPU-based embedding model
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model

async def get_or_generate_explanation(alert: Alert, db: AsyncSession) -> dict:
    """Gets cached threat explanation from Redis or DB, else calls OpenRouter to generate it."""
    cache_key = f"explain:{alert.alert_signature}"
    
    # 1. Try In-Memory Cache
    cached_val = await cache.get(cache_key)
    if cached_val:
        try:
            logger.info("Retrieved explanation from cache.")
            return json.loads(cached_val)
        except Exception:
            pass

    # 2. Try Database
    query = select(ThreatExplanation).where(
        ThreatExplanation.alert_signature == alert.alert_signature
    )
    result = await db.execute(query)
    explanation_db = result.scalars().first()
    
    # Verify expiration
    if explanation_db and explanation_db.expires_at > datetime.utcnow():
        data = {
            "explanation": explanation_db.explanation_text,
            "mitre_tactic": explanation_db.mitre_tactic,
            "mitre_technique_id": explanation_db.mitre_technique_id,
            "recommended_action": explanation_db.recommended_action,
            "cached": True,
            "model_used": explanation_db.model_used
        }
        # Write back to cache
        await cache.set(cache_key, json.dumps(data), ex=86400 * 7)
        logger.info("Retrieved explanation from DB and updated cache.")
        return data

    # 3. Generate New Explanation via OpenRouter RAG
    logger.info("Generating new explanation via OpenRouter...")
    data = await generate_explanation(alert, db)
    return data

async def generate_explanation(alert: Alert, db: AsyncSession) -> dict:
    """Performs local vector similarity search and queries OpenRouter API for Claude explanations."""
    # 1. Retrieve all knowledge base items
    kb_query = select(KnowledgeBase)
    kb_result = await db.execute(kb_query)
    kb_items = kb_result.scalars().all()
    
    relevant_intel = []
    
    if kb_items:
        try:
            # Get text to search
            query_text = f"{alert.title}. {alert.event_type}. Tactic: {alert.mitre_tactic or ''}."
            # Embed search query
            model = get_embedding_model()
            q_emb = np.array(model.encode(query_text)).reshape(1, -1)
            
            # Compute cosine similarity
            similarities = []
            for item in kb_items:
                item_emb = np.array(item.embedding).reshape(1, -1)
                sim = cosine_similarity(q_emb, item_emb)[0][0]
                similarities.append((sim, item))
            
            # Sort DESC
            similarities.sort(key=lambda x: x[0], reverse=True)
            # Take top 5
            top_5 = similarities[:5]
            
            relevant_intel = [
                {"title": item.title, "content": item.content[:500]}
                for _, item in top_5
            ]
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}", exc_info=True)
            # Fallback to keyword matching or empty if fails
            relevant_intel = [
                {"title": item.title, "content": item.content[:500]}
                for item in kb_items[:3]
            ]
            
    # 2. Build OpenRouter Chat Prompt
    system_prompt = (
        "You are a senior cybersecurity analyst.\n"
        "Given an alert and relevant threat intelligence, produce a concise threat explanation.\n"
        "You MUST respond ONLY with a JSON object. Do not include markdown code blocks like ```json.\n"
        "The JSON object must have exactly the following keys:\n"
        "{\n"
        '  "explanation": "string (max 150 words, plain English, what happened and why it is suspicious)",\n'
        '  "mitre_tactic": "string (tactic name)",\n'
        '  "mitre_technique_id": "string (e.g. T1048.003)",\n'
        '  "recommended_action": "string (one clear recommended next action)"\n'
        "}"
    )

    user_content = {
        "alert": {
            "title": alert.title,
            "source_ip": alert.source_ip,
            "dest_ip": alert.dest_ip,
            "event_type": alert.event_type,
            "anomaly_score": alert.anomaly_score,
            "severity": alert.severity,
            "event_count": alert.event_count,
            "first_seen": alert.first_seen_at.isoformat(),
            "last_seen": alert.last_seen_at.isoformat(),
        },
        "threat_intel": relevant_intel
    }

    fallback_explanation = {
        "explanation": f"Host {alert.source_ip} triggered a {alert.severity} alert due to unusual {alert.event_type} behaviors with an anomaly score of {alert.anomaly_score}.",
        "mitre_tactic": alert.mitre_tactic or "Initial Access",
        "mitre_technique_id": alert.mitre_technique_id or "T1190",
        "recommended_action": "Investigate raw log payloads and isolate host if outbound connections are unrecognized.",
        "cached": False,
        "model_used": "fallback-rule"
    }

    # 3. Connect to OpenRouter API
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not configured. Falling back to rule-based explanation.")
        return fallback_explanation

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Threat Analyzer",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_content)}
        ],
        "max_tokens": settings.LLM_MAX_TOKENS,
        "temperature": 0.2
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter returned status {response.status_code}: {response.text}")
                return fallback_explanation
                
            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"]
            
            # Clean possible markdown wrapping
            content_str = content.strip()
            if content_str.startswith("```"):
                lines = content_str.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content_str = "\n".join(lines).strip()
                
            parsed = json.loads(content_str)
            
            # Store in Database
            expires_at = datetime.utcnow() + timedelta(days=7)
            explanation_obj = ThreatExplanation(
                id=uuid.uuid4(),
                alert_signature=alert.alert_signature,
                explanation_text=parsed["explanation"],
                mitre_tactic=parsed["mitre_tactic"],
                mitre_technique_id=parsed["mitre_technique_id"],
                recommended_action=parsed["recommended_action"],
                model_used=settings.LLM_MODEL,
                prompt_version=1,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            db.add(explanation_obj)
            await db.commit()
            
            result_data = {
                "explanation": explanation_obj.explanation_text,
                "mitre_tactic": explanation_obj.mitre_tactic,
                "mitre_technique_id": explanation_obj.mitre_technique_id,
                "recommended_action": explanation_obj.recommended_action,
                "cached": False,
                "model_used": explanation_obj.model_used
            }
            
            # Cache in In-Memory Cache
            await cache.set(f"explain:{alert.alert_signature}", json.dumps(result_data), ex=86400 * 7)
            return result_data
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}", exc_info=True)
        return fallback_explanation
