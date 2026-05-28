import os
import sys
import asyncio
from datetime import datetime
import uuid

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.all_models import KnowledgeBase

# Core MITRE ATT&CK techniques list for RAG
ATTACK_TECHNIQUES = [
    {
        "source_type": "mitre_attack",
        "source_id": "T1048.003",
        "title": "Exfiltration Over Alternative Protocol - Exfiltration Over Unencrypted/Non-Application Protocol",
        "content": "Adversaries may steal data by transferring it over an alternative protocol than the primary command and control channel. The exfiltration event may occur over a different port or protocol than usual, such as transferring large files over DNS, ICMP, or custom protocols. Common behaviors include anomalies in outbound byte volumes and connections to unrecognized external IP addresses.",
        "metadata_json": {"tactic": "Exfiltration", "severity": "high"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1071.001",
        "title": "Application Layer Protocol - Web Protocols",
        "content": "Adversaries may communicate using application layer protocols associated with web traffic to avoid detection and blending in with normal network activity. Web protocols like HTTP or HTTPS are commonly used for command and control (C2). Beaconing behavior, regular request intervals, and connections to newly registered domains or known Tor exit nodes are typical indicators.",
        "metadata_json": {"tactic": "Command and Control", "severity": "high"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1021.001",
        "title": "Remote Services - Remote Desktop Protocol",
        "content": "Adversaries may log in to interactive remote desktops using RDP (Remote Desktop Protocol) to gain lateral movement within the network. RDP connections between internal hosts that do not typically communicate or outbound connections from unauthorized workstations are strong signals of compromise.",
        "metadata_json": {"tactic": "Lateral Movement", "severity": "medium"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1068",
        "title": "Exploitation for Privilege Escalation",
        "content": "Adversaries may exploit software vulnerabilities in local services or kernel components to elevate privileges to SYSTEM or Administrator. Indicators include system crashes, unauthorized service creations, or executions of abnormal processes from web servers or database services.",
        "metadata_json": {"tactic": "Privilege Escalation", "severity": "critical"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1098",
        "title": "Account Manipulation",
        "content": "Adversaries may manipulate accounts to maintain access to victim systems. This may include modifying account credentials, adding permission groups, or creating new backdoors. Indicators include unusual additions of users to domain administrator groups or password resets outside working hours.",
        "metadata_json": {"tactic": "Persistence", "severity": "high"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1003.001",
        "title": "OS Credential Dumping - LSASS Memory",
        "content": "Adversaries may attempt to access credential material from the Local Security Authority Subsystem Service (LSASS) process memory. Dumping LSASS memory allows extracting passwords, hashes, and Kerberos tickets. Typical indicators include executions of Mimikatz or procdump targeting lsass.exe.",
        "metadata_json": {"tactic": "Credential Access", "severity": "critical"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1036",
        "title": "Masquerading",
        "content": "Adversaries may disguise artifacts or names to evade security controls. This includes renaming executables to match legitimate system tools (e.g., svchost.exe), running from unusual paths (e.g., AppData), or spoofing certificates. Anomalous parent-child process relationships are key indicators.",
        "metadata_json": {"tactic": "Defense Evasion", "severity": "medium"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1082",
        "title": "System Information Discovery",
        "content": "Adversaries may attempt to get detailed information about the operating system and hardware configuration to map out the network structure. Commands like systeminfo, hostname, or whoami executed in rapid succession by service accounts indicate discovery behaviors.",
        "metadata_json": {"tactic": "Discovery", "severity": "low"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1595",
        "title": "Active Scanning",
        "content": "Adversaries may execute active scans to gather information about host configurations, open ports, and running services. Scan activities are characterized by high rates of port connections (SYN scans) or ping sweeps targeting multiple consecutive IP addresses.",
        "metadata_json": {"tactic": "Reconnaissance", "severity": "low"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1190",
        "title": "Exploitation of Public-Facing Application",
        "content": "Adversaries may exploit vulnerabilities in internet-facing software, such as web servers or VPN gateways, to gain initial access. Common exploit behaviors include directory traversal requests, SQL injection payloads, or remote code execution (RCE) patterns in raw web server log requests.",
        "metadata_json": {"tactic": "Initial Access", "severity": "critical"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1203",
        "title": "Exploitation for Client Execution",
        "content": "Adversaries may exploit vulnerabilities in user applications (such as email clients, web browsers, or PDF readers) to run arbitrary code. This typically happens when a user opens a malicious attachment or visits a compromised site.",
        "metadata_json": {"tactic": "Execution", "severity": "high"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1114",
        "title": "Email Collection",
        "content": "Adversaries may gather email data from servers, clients, or databases to steal sensitive communications. Behaviors include bulk downloading inbox folders, querying mail server APIs, or forward rules redirecting internal mail to external domains.",
        "metadata_json": {"tactic": "Collection", "severity": "medium"}
    },
    {
        "source_type": "mitre_attack",
        "source_id": "T1485",
        "title": "Data Destruction",
        "content": "Adversaries may destroy data to disrupt operations or cover their tracks. This includes wiping files, modifying master boot records (MBR), or running system-wide delete scripts. Strong indicators include rapid file system modification and process deletions.",
        "metadata_json": {"tactic": "Impact", "severity": "critical"}
    }
]

async def main():
    print("Initializing SentenceTransformer model (all-MiniLM-L6-v2)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Connecting to database...")
    async with SessionLocal() as db:
        for tech in ATTACK_TECHNIQUES:
            source_id = tech["source_id"]
            
            # Check if already exists
            from sqlalchemy.future import select
            query = select(KnowledgeBase).where(KnowledgeBase.source_id == source_id)
            result = await db.execute(query)
            existing = result.scalars().first()
            
            # Encode content
            text_to_embed = f"{tech['title']}. {tech['content']}"
            embedding = model.encode(text_to_embed).tolist()
            
            if existing:
                print(f"Updating technique {source_id}...")
                existing.title = tech["title"]
                existing.content = tech["content"]
                existing.embedding = embedding
                existing.metadata_json = tech["metadata_json"]
                existing.updated_at = datetime.utcnow()
            else:
                print(f"Inserting technique {source_id}...")
                db_kb = KnowledgeBase(
                    id=uuid.uuid4(),
                    source_type=tech["source_type"],
                    source_id=tech["source_id"],
                    title=tech["title"],
                    content=tech["content"],
                    embedding=embedding,
                    metadata_json=tech["metadata_json"]
                )
                db.add(db_kb)
        
        await db.commit()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
