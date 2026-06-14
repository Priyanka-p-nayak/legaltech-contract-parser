# contracts/services/risk_detector.py

# WHY THIS FILE EXISTS:
# Some contract clauses are extremely risky for businesses.
# Examples:
#   "Party A shall indemnify Party B for ANY and ALL losses" ← unlimited risk
#   "The penalty for delay is $10,000 per day" ← heavy financial risk
#   "This is an exclusive agreement" ← you can't work with anyone else
#
# This file scans every clause and flags risky language.
# It assigns a risk level (LOW / MEDIUM / HIGH) to each clause
# and then calculates an overall contract risk score.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

import re
import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── RISK RULES DICTIONARY ─────────────────────────────────────────────────────

# This is the core of the risk engine.
# Each key is a risk type name.
# Each value is a dict containing:
#   "keywords"    : words that suggest this risk
#   "risk_level"  : HIGH / MEDIUM / LOW
#   "description" : human-readable explanation for lawyers
#   "suggestion"  : what the lawyer should do about it

RISK_RULES = {

    "UNLIMITED_LIABILITY": {
        "keywords": [
            "any and all", "unlimited liability", "without limit",
            "all losses", "all damages", "full liability",
            "entire liability", "regardless of", "however caused",
            "irrespective of", "notwithstanding"
        ],
        "risk_level": "HIGH",
        "description": "This clause may expose a party to unlimited financial liability.",
        "suggestion": "Negotiate a liability cap equal to the contract value or insurance coverage."
    },

    "INDEMNIFICATION_RISK": {
        "keywords": [
            "indemnify", "indemnification", "hold harmless",
            "defend and indemnify", "full indemnity",
            "broad indemnity", "indemnified against all"
        ],
        "risk_level": "HIGH",
        "description": "Broad indemnification clause detected. Party may be required to cover all losses of the other party.",
        "suggestion": "Limit indemnification to direct losses caused by your own negligence. Remove 'any and all' language."
    },

    "PENALTY_CLAUSE": {
        "keywords": [
            "penalty", "penalties", "liquidated damages",
            "late fee", "interest per day", "per diem",
            "daily penalty", "fine", "forfeiture",
            "delay damages", "interest on late payment"
        ],
        "risk_level": "HIGH",
        "description": "Financial penalty clauses detected. Late performance or payment may trigger significant charges.",
        "suggestion": "Review penalty amounts. Ensure they are proportionate and capped. Add grace periods."
    },

    "EXCLUSIVITY_RISK": {
        "keywords": [
            "exclusive", "exclusively", "sole provider",
            "shall not engage", "not to hire", "non-compete",
            "exclusivity period", "restricted from",
            "only supplier", "preferred supplier"
        ],
        "risk_level": "MEDIUM",
        "description": "Exclusivity clause detected. This may restrict business with other clients or suppliers.",
        "suggestion": "Define the scope and duration of exclusivity clearly. Consider adding geographic or sector limits."
    },

    "AUTO_RENEWAL": {
        "keywords": [
            "automatically renew", "auto-renewal", "auto renewal",
            "shall automatically extend", "deemed renewed",
            "unless terminated", "rolling contract",
            "evergreen clause", "automatic extension"
        ],
        "risk_level": "MEDIUM",
        "description": "Auto-renewal clause detected. Contract may renew without explicit action.",
        "suggestion": "Add a calendar reminder before the notice deadline. Ensure renewal terms are acceptable."
    },

    "UNILATERAL_CHANGES": {
        "keywords": [
            "reserves the right to change", "may modify",
            "may amend", "at its sole discretion",
            "without notice", "unilaterally",
            "right to alter", "change terms at any time"
        ],
        "risk_level": "HIGH",
        "description": "One party can change contract terms unilaterally without consent.",
        "suggestion": "Require mutual written consent for any changes. Ensure notice period for changes."
    },

    "TERMINATION_FOR_CONVENIENCE": {
        "keywords": [
            "terminate for convenience", "terminate without cause",
            "termination for convenience", "at will termination",
            "may terminate at any time", "terminate at its discretion"
        ],
        "risk_level": "MEDIUM",
        "description": "Either party can terminate without reason. May affect business planning.",
        "suggestion": "Add a minimum notice period (e.g., 90 days) and compensation for early termination."
    },

    "INTELLECTUAL_PROPERTY_RISK": {
        "keywords": [
            "all intellectual property", "assign all rights",
            "work for hire", "transfers ownership",
            "all inventions", "all creations",
            "irrevocable assignment", "perpetual license"
        ],
        "risk_level": "HIGH",
        "description": "Broad IP ownership transfer detected. You may lose rights to your own work.",
        "suggestion": "Clearly define what IP is covered. Retain rights to pre-existing IP and general methodologies."
    },

    "GOVERNING_LAW_RISK": {
        "keywords": [
            "laws of a foreign country", "foreign jurisdiction",
            "international arbitration", "overseas courts"
        ],
        "risk_level": "LOW",
        "description": "Contract may be governed by foreign law, increasing legal costs.",
        "suggestion": "Negotiate for your home country jurisdiction or neutral international arbitration."
    },

    "UNLIMITED_INDEMNITY": {
        "keywords": [
            "indemnify for any loss", "indemnify for all loss",
            "all claims whatsoever", "all damages whatsoever",
            "without any limitation", "full and complete indemnity"
        ],
        "risk_level": "HIGH",
        "description": "Unlimited indemnity with no cap. Extreme financial exposure.",
        "suggestion": "This is a critical clause. Negotiate immediately to add a liability cap."
    },
}


# ── FUNCTION 1: DETECT RISKS IN A SINGLE CLAUSE ──────────────────────────────

def detect_risks_in_clause(clause_text):
    """
    Scan a single clause for all risk types.

    For each risk type, check if any keywords appear in the clause.
    Return a list of all risks found.

    Arguments:
        clause_text (str): The text of one clause

    Returns:
        list of dict: Each dict describes one risk found
        Example:
        [
            {
                "risk_type": "INDEMNIFICATION_RISK",
                "risk_level": "HIGH",
                "description": "Broad indemnification...",
                "matched_keywords": ["indemnify", "hold harmless"],
                "suggestion": "Limit indemnification..."
            }
        ]
    """

    if not clause_text:
        return []

    text_lower = clause_text.lower()
    risks_found = []

    # Check every risk rule
    for risk_type, rule in RISK_RULES.items():

        matched_keywords = []

        # Check each keyword for this risk type
        for keyword in rule["keywords"]:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)

        # If ANY keywords matched, this risk is present
        if matched_keywords:
            risk_entry = {
                "risk_type":        risk_type,
                "risk_level":       rule["risk_level"],
                "description":      rule["description"],
                "suggestion":       rule["suggestion"],
                "matched_keywords": matched_keywords,
            }
            risks_found.append(risk_entry)
            logger.debug(f"Risk detected: {risk_type} — keywords: {matched_keywords}")

    return risks_found


# ── FUNCTION 2: CALCULATE OVERALL RISK LEVEL ─────────────────────────────────

def calculate_overall_risk(all_risks):
    """
    Calculate one overall risk level for the whole contract.

    Rules:
    - If ANY HIGH risk exists → overall = HIGH
    - If ANY MEDIUM risk exists (but no HIGH) → overall = MEDIUM
    - If only LOW risks → overall = LOW
    - If no risks → overall = LOW

    Arguments:
        all_risks (list): All risk dicts found across all clauses

    Returns:
        str: "HIGH", "MEDIUM", or "LOW"
    """

    if not all_risks:
        return "LOW"

    # Collect all risk levels found
    risk_levels = [risk["risk_level"] for risk in all_risks]

    if "HIGH" in risk_levels:
        return "HIGH"
    elif "MEDIUM" in risk_levels:
        return "MEDIUM"
    else:
        return "LOW"


# ── FUNCTION 3: SCAN ENTIRE CONTRACT ─────────────────────────────────────────

def scan_contract_for_risks(categorized_clauses):
    """
    Scan every clause of the contract for risks.

    This is the master risk detection function.
    It goes through each categorized clause and runs risk detection.

    Arguments:
        categorized_clauses (list): Output from clause_categorizer.py
        Each item: {"heading": "...", "content": "...", "category": "..."}

    Returns:
        dict: Complete risk analysis report
        {
            "overall_risk_level": "HIGH",
            "total_risks_found": 5,
            "high_risk_count": 2,
            "medium_risk_count": 2,
            "low_risk_count": 1,
            "risky_clauses": [...],
            "all_risks": [...]
        }
    """

    logger.info("Starting contract risk scan...")

    all_risks = []         # All risks found across the entire contract
    risky_clauses = []     # Clauses that have at least one risk

    for clause in categorized_clauses:

        content = clause.get("content", "")
        heading = clause.get("heading", "")

        # Run risk detection on this clause
        clause_risks = detect_risks_in_clause(content)

        if clause_risks:
            # This clause has risks — add to risky clauses list
            risky_clause_entry = {
                "heading":     heading,
                "content":     content[:300],  # First 300 chars for preview
                "category":    clause.get("category", "GENERAL"),
                "risks_found": clause_risks
            }
            risky_clauses.append(risky_clause_entry)

            # Add all risks from this clause to the master list
            all_risks.extend(clause_risks)

    # Calculate overall risk level
    overall_risk = calculate_overall_risk(all_risks)

    # Count risks by severity
    high_count   = sum(1 for r in all_risks if r["risk_level"] == "HIGH")
    medium_count = sum(1 for r in all_risks if r["risk_level"] == "MEDIUM")
    low_count    = sum(1 for r in all_risks if r["risk_level"] == "LOW")

    # Build the complete report
    report = {
        "overall_risk_level":  overall_risk,
        "total_risks_found":   len(all_risks),
        "high_risk_count":     high_count,
        "medium_risk_count":   medium_count,
        "low_risk_count":      low_count,
        "risky_clauses":       risky_clauses,
        "all_risks":           all_risks,
    }

    logger.info(
        f"Risk scan complete: {overall_risk} risk — "
        f"{high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW"
    )

    return report