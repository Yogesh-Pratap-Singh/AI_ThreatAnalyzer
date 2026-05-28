TACTIC_WEIGHTS = {
    "Exfiltration": 0.90,
    "Impact": 0.90,
    "Command and Control": 0.85,
    "Lateral Movement": 0.80,
    "Privilege Escalation": 0.75,
    "Persistence": 0.70,
    "Credential Access": 0.70,
    "Defense Evasion": 0.65,
    "Discovery": 0.40,
    "Reconnaissance": 0.35,
    "Initial Access": 0.60,
    "Execution": 0.65,
    "Collection": 0.55,
}

def compute_severity_score(
    anomaly_score: float,
    intel_match_score: float = 0.0,
    tactic_weight: float = 0.0,
    asset_criticality: float = 0.5
) -> float:
    """
    Computes a composite severity score between 0.0 and 1.0 using the formula:
    anomaly_score * 0.40 + intel_match_score * 0.30 + tactic_weight * 0.20 + asset_criticality * 0.10
    """
    score = (
        anomaly_score * 0.40 +
        intel_match_score * 0.30 +
        tactic_weight * 0.20 +
        asset_criticality * 0.10
    )
    return round(min(max(score, 0.0), 1.0), 4)

def score_to_severity(score: float) -> str:
    """Classifies a score into a severity tier."""
    if score >= 0.85:
        return "critical"
    elif score >= 0.65:
        return "high"
    elif score >= 0.40:
        return "medium"
    return "low"

def get_tactic_weight(tactic_name: str) -> float:
    if not tactic_name:
        return 0.0
    return TACTIC_WEIGHTS.get(tactic_name, 0.0)
