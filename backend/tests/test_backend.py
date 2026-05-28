import pytest
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.cache import InMemoryCache
from app.core.security import get_password_hash, verify_password
from app.services.severity_service import compute_severity_score, score_to_severity, get_tactic_weight

@pytest.mark.asyncio
async def test_in_memory_cache():
    cache = InMemoryCache()
    # Test set and get
    await cache.set("test_key", "test_val", ex=2)
    val = await cache.get("test_key")
    assert val == "test_val"

    # Test incr
    count = await cache.incr("counter")
    assert count == 1
    count = await cache.incr("counter")
    assert count == 2

    # Test expire
    await cache.expire("counter", 1)
    # Check delete
    deleted = await cache.delete("test_key")
    assert deleted == 1
    val = await cache.get("test_key")
    assert val is None

def test_password_hashing():
    password = "MySecurePassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_severity_scoring():
    # Formula: anomaly_score * 0.40 + intel_match_score * 0.30 + tactic_weight * 0.20 + asset_criticality * 0.10
    # Inputs: 0.8, 0.5, 0.9 (Exfiltration), 1.0 (Critical Asset)
    # 0.8 * 0.4 + 0.5 * 0.3 + 0.9 * 0.2 + 1.0 * 0.1 = 0.32 + 0.15 + 0.18 + 0.1 = 0.75
    score = compute_severity_score(
        anomaly_score=0.8,
        intel_match_score=0.5,
        tactic_weight=0.9,
        asset_criticality=1.0
    )
    assert score == 0.75
    assert score_to_severity(score) == "high"

    # Critical tier (>= 0.85)
    crit_score = compute_severity_score(
        anomaly_score=0.95,
        intel_match_score=0.9,
        tactic_weight=0.9,
        asset_criticality=1.0
    )
    assert crit_score >= 0.85
    assert score_to_severity(crit_score) == "critical"

    # Low tier (< 0.40)
    low_score = compute_severity_score(
        anomaly_score=0.2,
        intel_match_score=0.1,
        tactic_weight=0.35, # Reconnaissance
        asset_criticality=0.2
    )
    assert low_score < 0.40
    assert score_to_severity(low_score) == "low"

def test_cosine_similarity():
    # Simple scikit-learn cosine similarity validation
    vec_a = np.array([1.0, 0.0, 1.0]).reshape(1, -1)
    vec_b = np.array([1.0, 0.0, 1.0]).reshape(1, -1)
    sim = cosine_similarity(vec_a, vec_b)[0][0]
    assert pytest.approx(sim, 0.0001) == 1.0

    vec_c = np.array([-1.0, 0.0, -1.0]).reshape(1, -1)
    sim_neg = cosine_similarity(vec_a, vec_c)[0][0]
    assert pytest.approx(sim_neg, 0.0001) == -1.0
