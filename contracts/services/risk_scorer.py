# contracts/services/risk_scorer.py

# WHY THIS FILE EXISTS:
# Our Week 2 risk_detector.py finds risks and labels them HIGH/MEDIUM/LOW.
# But lawyers need more precision:
#   "This contract scored 82/100 risk — critical review needed"
#   "Clause 3 is the most dangerous clause (score: 95)"
#
# This file:
#   1. Assigns numerical weights to each risk type
#   2. Calculates a score per clause (0-100)
#   3. Calculates an overall contract risk score (0-100)
#   4. Ranks clauses from most to least risky
#   5. Generates actionable recommendations

# ── IMPORTS ───────────────────────────────────────────────────────────────────

import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── RISK WEIGHT TABLE ─────────────────────────────────────────────────────────

# Each risk type gets a weight (0-100).
# Higher weight = more dangerous risk.
# These weights are based on common legal practice:
#   - Unlimited liability is the most dangerous (weight 95)
#   - A governing law issue is less critical (weight 20)
#
# The weight becomes the clause's contribution to the overall score.

RISK_WEIGHTS = {
    # ── CRITICAL RISKS (weight 80-100) ──────────────────────────────────────
    
    "UNLIMITED_LIABILITY": {
        "weight":      95,
        "severity":    "CRITICAL",
        "priority":    1,        # 1 = highest priority to review
        "category":    "Financial Exposure"
    },
    "UNLIMITED_INDEMNITY": {
        "weight":      90,
        "severity":    "CRITICAL",
        "priority":    1,
        "category":    "Financial Exposure"
    },
    "UNILATERAL_CHANGES": {
        "weight":      85,
        "severity":    "CRITICAL",
        "priority":    2,
        "category":    "Contract Control"
    },
    "INTELLECTUAL_PROPERTY_RISK": {
        "weight":      85,
        "severity":    "CRITICAL",
        "priority":    2,
        "category":    "IP Rights"
    },
    
    # ── HIGH RISKS (weight 60-79) ────────────────────────────────────────────
    
    "INDEMNIFICATION_RISK": {
        "weight":      75,
        "severity":    "HIGH",
        "priority":    3,
        "category":    "Financial Exposure"
    },
    "PENALTY_CLAUSE": {
        "weight":      70,
        "severity":    "HIGH",
        "priority":    3,
        "category":    "Financial Penalties"
    },
    
    # ── MEDIUM RISKS (weight 35-59) ──────────────────────────────────────────
    
    "EXCLUSIVITY_RISK": {
        "weight":      50,
        "severity":    "MEDIUM",
        "priority":    4,
        "category":    "Business Restriction"
    },
    "TERMINATION_FOR_CONVENIENCE": {
        "weight":      45,
        "severity":    "MEDIUM",
        "priority":    4,
        "category":    "Contract Stability"
    },
    "AUTO_RENEWAL": {
        "weight":      40,
        "severity":    "MEDIUM",
        "priority":    5,
        "category":    "Contract Duration"
    },
    
    # ── LOW RISKS (weight 1-34) ──────────────────────────────────────────────
    
    "GOVERNING_LAW_RISK": {
        "weight":      20,
        "severity":    "LOW",
        "priority":    6,
        "category":    "Jurisdiction"
    },
}

# ── DEFAULT WEIGHT for unknown risk types ─────────────────────────────────────
DEFAULT_RISK_WEIGHT = 30


# ── FUNCTION 1: SCORE A SINGLE CLAUSE ────────────────────────────────────────

def score_clause(clause_risks):
    """
    Calculate a numerical risk score for a single clause.
    
    The score is based on the highest-weight risk found in the clause.
    If multiple risks exist, we take the maximum (not the sum)
    because each risk is independent — they don't compound linearly.
    
    However, having MULTIPLE risks in one clause increases the score
    slightly (multiplier effect).
    
    Arguments:
        clause_risks (list): List of risk dicts from risk_detector.py
                             Each has: risk_type, risk_level, description
    
    Returns:
        dict: Score information
        {
            "score": 85,               ← 0 to 100
            "severity": "CRITICAL",
            "risk_count": 2,
            "primary_risk": "UNLIMITED_LIABILITY",
            "score_breakdown": [...]
        }
    """
    
    if not clause_risks:
        return {
            "score":          0,
            "severity":       "NONE",
            "risk_count":     0,
            "primary_risk":   None,
            "score_breakdown": []
        }
    
    # ── STEP 1: GET WEIGHTS FOR EACH RISK ─────────────────────────────────────
    
    scored_risks = []
    
    for risk in clause_risks:
        risk_type = risk.get("risk_type", "UNKNOWN")
        
        # Look up the weight for this risk type
        # Use DEFAULT_RISK_WEIGHT if it's not in our table
        weight_info = RISK_WEIGHTS.get(risk_type, {})
        weight = weight_info.get("weight", DEFAULT_RISK_WEIGHT)
        
        scored_risks.append({
            "risk_type": risk_type,
            "weight":    weight,
            "severity":  weight_info.get("severity", "MEDIUM"),
            "category":  weight_info.get("category", "General"),
            "priority":  weight_info.get("priority", 5),
        })
    
    # ── STEP 2: FIND THE PRIMARY (HIGHEST WEIGHT) RISK ───────────────────────
    
    # Sort by weight descending — highest weight first
    scored_risks.sort(key=lambda x: x["weight"], reverse=True)
    
    # The primary risk is the most dangerous one
    primary = scored_risks[0]
    base_score = primary["weight"]
    
    # ── STEP 3: APPLY MULTIPLIER FOR MULTIPLE RISKS ───────────────────────────
    
    # Having 2+ risks in one clause makes it slightly more dangerous
    # Each extra risk adds 2% to the score, capped at 100
    extra_risks = len(scored_risks) - 1  # number of risks beyond the first
    multiplier  = 1 + (extra_risks * 0.02)  # e.g. 3 extra risks → 1.06
    
    # Calculate final score, capped at 100
    final_score = min(100, int(base_score * multiplier))
    
    return {
        "score":           final_score,
        "severity":        primary["severity"],
        "risk_count":      len(scored_risks),
        "primary_risk":    primary["risk_type"],
        "primary_category": primary["category"],
        "score_breakdown": scored_risks
    }


# ── FUNCTION 2: SCORE THE ENTIRE CONTRACT ────────────────────────────────────

def score_entire_contract(risky_clauses):
    """
    Calculate the overall risk score for the entire contract.
    
    Method:
    1. Score each risky clause individually
    2. The overall score = weighted average of clause scores
       (with highest-scored clauses weighted more)
    3. If there are CRITICAL risks, apply a minimum floor score
    
    Arguments:
        risky_clauses (list): List of clauses with their risks
                              From risk_detector.scan_contract_for_risks()
    
    Returns:
        dict: Overall contract risk assessment
        {
            "overall_score": 78,
            "risk_grade": "B",
            "overall_level": "HIGH",
            "scored_clauses": [...],
            "top_risky_clauses": [...],
            "critical_issues": [...]
        }
    """
    
    if not risky_clauses:
        logger.info("No risky clauses found — contract score is 0")
        return {
            "overall_score":     0,
            "risk_grade":        "A+",
            "overall_level":     "LOW",
            "scored_clauses":    [],
            "top_risky_clauses": [],
            "critical_issues":   [],
            "recommendation":    "Contract appears low risk. Standard review recommended."
        }
    
    # ── STEP 1: SCORE EACH RISKY CLAUSE ──────────────────────────────────────
    
    scored_clauses = []
    
    for clause in risky_clauses:
        
        clause_risks   = clause.get("risks_found", [])
        clause_heading = clause.get("heading", "Unknown Clause")
        clause_content = clause.get("content", "")
        
        # Get the score for this clause
        clause_score_info = score_clause(clause_risks)
        
        scored_clauses.append({
            "heading":       clause_heading,
            "content":       clause_content[:200],   # preview only
            "score":         clause_score_info["score"],
            "severity":      clause_score_info["severity"],
            "risk_count":    clause_score_info["risk_count"],
            "primary_risk":  clause_score_info["primary_risk"],
            "score_breakdown": clause_score_info["score_breakdown"]
        })
    
    # ── STEP 2: SORT CLAUSES BY SCORE (most dangerous first) ─────────────────
    
    scored_clauses.sort(key=lambda x: x["score"], reverse=True)
    
    # ── STEP 3: CALCULATE OVERALL CONTRACT SCORE ──────────────────────────────
    
    # We use a weighted average where higher-scored clauses count more
    # This ensures one extremely bad clause raises the overall score significantly
    
    total_weighted_score = 0
    total_weight         = 0
    
    for i, clause in enumerate(scored_clauses):
        
        clause_score = clause["score"]
        
        # Weight decreases for each subsequent clause
        # Clause 1 (most dangerous) has weight 10
        # Clause 2 has weight 9, Clause 3 has weight 8, etc.
        # Minimum weight is 1
        position_weight = max(1, 10 - i)
        
        total_weighted_score += clause_score * position_weight
        total_weight         += position_weight
    
    # Calculate weighted average
    if total_weight > 0:
        overall_score = int(total_weighted_score / total_weight)
    else:
        overall_score = 0
    
    # ── STEP 4: APPLY CRITICAL RISK FLOOR ────────────────────────────────────
    
    # If any clause has a CRITICAL severity, the overall score
    # must be at least 70 (regardless of the weighted average)
    # because critical risks are always serious
    has_critical = any(c["severity"] == "CRITICAL" for c in scored_clauses)
    if has_critical:
        overall_score = max(overall_score, 70)
    
    # Cap at 100
    overall_score = min(100, overall_score)
    
    # ── STEP 5: ASSIGN RISK GRADE AND LEVEL ──────────────────────────────────
    
    risk_grade, overall_level, recommendation = _get_grade_and_level(overall_score)
    
    # ── STEP 6: COLLECT CRITICAL ISSUES ──────────────────────────────────────
    
    # Critical issues are the highest priority items to fix
    critical_issues = [
        c for c in scored_clauses
        if c["severity"] in ("CRITICAL", "HIGH")
    ]
    
    logger.info(
        f"Contract scored: {overall_score}/100 "
        f"({risk_grade}) — {overall_level}"
    )
    
    return {
        "overall_score":     overall_score,
        "risk_grade":        risk_grade,
        "overall_level":     overall_level,
        "scored_clauses":    scored_clauses,
        "top_risky_clauses": scored_clauses[:5],   # top 5 most dangerous
        "critical_issues":   critical_issues,
        "recommendation":    recommendation,
        "has_critical_risk": has_critical,
    }


# ── FUNCTION 3: GET GRADE AND LEVEL ──────────────────────────────────────────

def _get_grade_and_level(score):
    """
    Convert a numerical score to a letter grade,
    risk level, and recommendation.
    
    Grading scale:
    A+ (0-10)   = Excellent — very low risk
    A  (11-25)  = Good — minor concerns
    B  (26-45)  = Acceptable — review recommended
    C  (46-65)  = Concerning — several risks present
    D  (66-80)  = Dangerous — legal review required
    F  (81-100) = Critical — do not sign without major revisions
    
    Arguments:
        score (int): 0 to 100
    
    Returns:
        tuple: (grade, level, recommendation)
    """
    
    if score <= 10:
        return (
            "A+",
            "LOW",
            "Excellent contract. Very low risk. Standard review sufficient."
        )
    elif score <= 25:
        return (
            "A",
            "LOW",
            "Good contract. Minor concerns noted. Proceed with standard review."
        )
    elif score <= 45:
        return (
            "B",
            "LOW",
            "Acceptable contract. A few clauses need attention. Review before signing."
        )
    elif score <= 65:
        return (
            "C",
            "MEDIUM",
            "Several risk clauses detected. Legal review strongly recommended."
        )
    elif score <= 80:
        return (
            "D",
            "HIGH",
            "Dangerous contract. Multiple high-risk clauses. Do not sign without negotiation."
        )
    else:
        return (
            "F",
            "HIGH",
            "CRITICAL: Extreme risk level. Major revisions required before signing."
        )