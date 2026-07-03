# contracts/services/report_generator.py

# WHY THIS FILE EXISTS:
# After all analysis is done, lawyers need a REPORT they can read.
# This file assembles everything into one clean, structured document:
#
#   EXECUTIVE SUMMARY
#   PARTIES INVOLVED
#   KEY DATES AND DURATION
#   RISK SCORE: 82/100 (Grade F)
#   TOP 5 RISKS
#   CLAUSE-BY-CLAUSE ANALYSIS
#   RECOMMENDATIONS
#
# The report is returned as both a Python dict (for the API/database)
# and as a formatted text string (for display or download).

# ── IMPORTS ───────────────────────────────────────────────────────────────────

from datetime import datetime
import logging

# Import our scoring engine
from contracts.services.risk_scorer import score_entire_contract

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


# ── FUNCTION 1: GENERATE FULL REPORT DICT ────────────────────────────────────

def generate_risk_report(
    entities,
    categorized_clauses,
    risk_scan_result,
    metadata=None
):
    """
    Generate a complete, structured risk report as a Python dictionary.
    
    This is the MASTER report function. It combines:
    - Entity extraction results (companies, dates, jurisdiction)
    - Clause categorization results
    - Risk detection results
    - Advanced risk scores
    
    Arguments:
        entities         (dict): From entity_extractor.extract_all_entities()
        categorized_clauses (list): From clause_categorizer.categorize_all_clauses()
        risk_scan_result (dict): From risk_detector.scan_contract_for_risks()
        metadata         (dict): From pdf_extractor.get_pdf_metadata() — optional
    
    Returns:
        dict: Complete structured report ready to save to DB or return via API
    """
    
    logger.info("Generating complete risk report...")
    
    # ── SECTION 1: REPORT HEADER ──────────────────────────────────────────────
    
    report_header = {
        # When was this report generated?
        "generated_at":   datetime.now().isoformat(),
        
        # Report version — useful when the NLP model is updated
        "report_version": "1.0",
        
        # Engine that produced this report
        "engine":         "LegalTech NLP Engine v1.0",
    }
    
    # ── SECTION 2: CONTRACT OVERVIEW ──────────────────────────────────────────
    
    # Safely extract entity data with defaults
    company_names     = entities.get("company_names", [])
    dates_found       = entities.get("dates", [])
    jurisdiction      = entities.get("jurisdiction", "Not specified")
    contract_duration = entities.get("contract_duration", "Not specified")
    
    contract_overview = {
        "parties":             company_names,
        "total_parties":       len(company_names),
        "dates_mentioned":     dates_found,
        "total_dates":         len(dates_found),
        "jurisdiction":        jurisdiction,
        "contract_duration":   contract_duration,
        "total_pages":         (metadata or {}).get("pages", "Unknown"),
        "document_title":      (metadata or {}).get("title", "Untitled Contract"),
    }
    
    # ── SECTION 3: CLAUSE ANALYSIS SUMMARY ───────────────────────────────────
    
    # Count how many clauses of each category were found
    category_counts = {}
    for clause in categorized_clauses:
        category = clause.get("category", "GENERAL")
        category_counts[category] = category_counts.get(category, 0) + 1
    
    clause_summary = {
        "total_clauses":     len(categorized_clauses),
        "category_breakdown": category_counts,
        
        # Which high-risk categories are present?
        "risky_categories":  [
            cat for cat in category_counts
            if cat in (
                "INDEMNIFICATION", "LIABILITY", "PENALTIES",
                "EXCLUSIVITY", "INTELLECTUAL_PROPERTY"
            )
        ]
    }
    
    # ── SECTION 4: ADVANCED RISK SCORING ─────────────────────────────────────
    
    # Get the risky clauses from the scan result
    risky_clauses = risk_scan_result.get("risky_clauses", [])
    
    # Run the advanced scoring engine
    score_result = score_entire_contract(risky_clauses)
    
    risk_score_section = {
        "overall_score":     score_result["overall_score"],
        "risk_grade":        score_result["risk_grade"],
        "overall_level":     score_result["overall_level"],
        "has_critical_risk": score_result["has_critical_risk"],
        "recommendation":    score_result["recommendation"],
        
        # Breakdown counts from basic scan
        "total_risks_found": risk_scan_result.get("total_risks_found", 0),
        "high_risk_count":   risk_scan_result.get("high_risk_count", 0),
        "medium_risk_count": risk_scan_result.get("medium_risk_count", 0),
        "low_risk_count":    risk_scan_result.get("low_risk_count", 0),
    }
    
    # ── SECTION 5: TOP RISKS ──────────────────────────────────────────────────
    
    # The top 5 most dangerous clauses
    top_risky_clauses = score_result.get("top_risky_clauses", [])
    
    # All individual risk instances found across the contract
    all_risks = risk_scan_result.get("all_risks", [])
    
    # Deduplicate risks by type (show each risk type once)
    seen_types   = set()
    unique_risks = []
    for risk in all_risks:
        risk_type = risk.get("risk_type")
        if risk_type not in seen_types:
            seen_types.add(risk_type)
            unique_risks.append(risk)
    
    top_risks_section = {
        # Top 5 most dangerous clauses (with scores)
        "top_5_risky_clauses": top_risky_clauses,
        
        # Unique risk types found (deduplicated)
        "unique_risk_types":   unique_risks,
        
        # Critical issues requiring immediate attention
        "critical_issues":     score_result.get("critical_issues", []),
    }
    
    # ── SECTION 6: RECOMMENDATIONS ───────────────────────────────────────────
    
    recommendations = _build_recommendations(
        all_risks, score_result["overall_score"]
    )
    
    # ── SECTION 7: SCORED CLAUSES (full list) ────────────────────────────────
    
    scored_clauses = score_result.get("scored_clauses", [])
    
    # ── ASSEMBLE COMPLETE REPORT ──────────────────────────────────────────────
    
    complete_report = {
        "header":            report_header,
        "contract_overview": contract_overview,
        "clause_summary":    clause_summary,
        "risk_score":        risk_score_section,
        "top_risks":         top_risks_section,
        "scored_clauses":    scored_clauses,
        "recommendations":   recommendations,
    }
    
    logger.info(
        f"Report generated — Score: {score_result['overall_score']}/100 "
        f"Grade: {score_result['risk_grade']}"
    )
    
    return complete_report


# ── FUNCTION 2: BUILD RECOMMENDATIONS ────────────────────────────────────────

def _build_recommendations(all_risks, overall_score):
    """
    Build a list of specific, actionable recommendations
    based on the risks found.
    
    Arguments:
        all_risks     (list): All risks found in the contract
        overall_score (int): The overall contract risk score
    
    Returns:
        list of dict: Each recommendation with priority and action
    """
    
    recommendations = []
    
    # Collect all risk types found
    risk_types_found = {risk.get("risk_type") for risk in all_risks}
    
    # ── RECOMMENDATION RULES ──────────────────────────────────────────────────
    
    # Each rule: if this risk type is present, add this recommendation
    
    recommendation_rules = [
        {
            "trigger":  "UNLIMITED_LIABILITY",
            "priority": "CRITICAL",
            "action":   "Negotiate a liability cap. Set the maximum liability to the total contract value or your insurance coverage amount.",
            "clause":   "Limitation of Liability"
        },
        {
            "trigger":  "UNLIMITED_INDEMNITY",
            "priority": "CRITICAL",
            "action":   "Remove 'any and all losses' language. Limit indemnification to direct losses caused by your own proven negligence only.",
            "clause":   "Indemnification"
        },
        {
            "trigger":  "INDEMNIFICATION_RISK",
            "priority": "HIGH",
            "action":   "Add mutual indemnification or limit the scope. Ensure indemnity is proportional to your role in the contract.",
            "clause":   "Indemnification"
        },
        {
            "trigger":  "PENALTY_CLAUSE",
            "priority": "HIGH",
            "action":   "Review penalty amounts. Ensure they are reasonable and proportionate. Add grace periods (minimum 5 business days) before penalties apply.",
            "clause":   "Penalties"
        },
        {
            "trigger":  "EXCLUSIVITY_RISK",
            "priority": "MEDIUM",
            "action":   "Limit exclusivity scope by geography, product category, or time period. Add minimum performance requirements from the other party.",
            "clause":   "Exclusivity"
        },
        {
            "trigger":  "AUTO_RENEWAL",
            "priority": "MEDIUM",
            "action":   "Set a calendar reminder 60 days before the contract end date to decide on renewal. Negotiate a minimum 30-day notice period for termination.",
            "clause":   "Term and Renewal"
        },
        {
            "trigger":  "UNILATERAL_CHANGES",
            "priority": "CRITICAL",
            "action":   "Remove the right to change terms unilaterally. All changes must require mutual written agreement. Add a minimum 30-day notice period.",
            "clause":   "Amendments"
        },
        {
            "trigger":  "INTELLECTUAL_PROPERTY_RISK",
            "priority": "CRITICAL",
            "action":   "Explicitly carve out pre-existing IP. Retain rights to general methodologies and tools. Limit IP transfer to work specifically created for this contract.",
            "clause":   "Intellectual Property"
        },
        {
            "trigger":  "TERMINATION_FOR_CONVENIENCE",
            "priority": "MEDIUM",
            "action":   "Negotiate minimum notice periods (90 days recommended). Add financial compensation for early termination to protect invested resources.",
            "clause":   "Termination"
        },
        {
            "trigger":  "GOVERNING_LAW_RISK",
            "priority": "LOW",
            "action":   "Consider negotiating for your home jurisdiction or a neutral international arbitration forum to reduce legal costs.",
            "clause":   "Governing Law"
        },
    ]
    
    # ── APPLY RULES ───────────────────────────────────────────────────────────
    
    for rule in recommendation_rules:
        if rule["trigger"] in risk_types_found:
            recommendations.append({
                "priority":     rule["priority"],
                "action":       rule["action"],
                "related_clause": rule["clause"],
                "risk_type":    rule["trigger"],
            })
    
    # ── ADD GENERAL RECOMMENDATION BASED ON SCORE ─────────────────────────────
    
    if overall_score >= 81:
        recommendations.insert(0, {
            "priority":       "CRITICAL",
            "action":         "DO NOT SIGN this contract without immediate legal counsel review. Risk score is extremely high.",
            "related_clause": "General",
            "risk_type":      "OVERALL_RISK"
        })
    elif overall_score >= 66:
        recommendations.insert(0, {
            "priority":       "HIGH",
            "action":         "Legal review is strongly recommended before signing. Multiple high-risk clauses require negotiation.",
            "related_clause": "General",
            "risk_type":      "OVERALL_RISK"
        })
    
    # Sort by priority: CRITICAL → HIGH → MEDIUM → LOW
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))
    
    return recommendations


# ── FUNCTION 3: GENERATE TEXT REPORT ─────────────────────────────────────────

def generate_text_report(complete_report):
    """
    Convert the report dictionary into a human-readable text format.
    
    This is what lawyers actually READ.
    Member 3 can display this in the dashboard or allow download as .txt
    
    Arguments:
        complete_report (dict): Output from generate_risk_report()
    
    Returns:
        str: Formatted text report
    """
    
    # Helper: make a section divider line
    def divider(char="=", length=60):
        return char * length
    
    lines = []
    
    # ── HEADER ────────────────────────────────────────────────────────────────
    
    lines.append(divider())
    lines.append("       LEGALTECH CONTRACT RISK ANALYSIS REPORT")
    lines.append(divider())
    
    header      = complete_report.get("header", {})
    risk_score  = complete_report.get("risk_score", {})
    overview    = complete_report.get("contract_overview", {})
    
    lines.append(f"Generated : {header.get('generated_at', 'N/A')}")
    lines.append(f"Engine    : {header.get('engine', 'N/A')}")
    lines.append("")
    
    # ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────────
    
    lines.append(divider("-"))
    lines.append("EXECUTIVE SUMMARY")
    lines.append(divider("-"))
    
    score = risk_score.get("overall_score", 0)
    grade = risk_score.get("risk_grade", "N/A")
    level = risk_score.get("overall_level", "UNKNOWN")
    
    lines.append(f"  Risk Score    : {score}/100")
    lines.append(f"  Risk Grade    : {grade}")
    lines.append(f"  Risk Level    : {level}")
    lines.append(f"  Total Risks   : {risk_score.get('total_risks_found', 0)}")
    lines.append(f"  HIGH risks    : {risk_score.get('high_risk_count', 0)}")
    lines.append(f"  MEDIUM risks  : {risk_score.get('medium_risk_count', 0)}")
    lines.append(f"  LOW risks     : {risk_score.get('low_risk_count', 0)}")
    lines.append("")
    lines.append(f"  RECOMMENDATION: {risk_score.get('recommendation', '')}")
    lines.append("")
    
    # ── CONTRACT OVERVIEW ─────────────────────────────────────────────────────
    
    lines.append(divider("-"))
    lines.append("CONTRACT OVERVIEW")
    lines.append(divider("-"))
    
    parties = overview.get("parties", [])
    if parties:
        lines.append("  PARTIES:")
        for i, party in enumerate(parties, 1):
            lines.append(f"    {i}. {party}")
    else:
        lines.append("  PARTIES: Not identified")
    
    lines.append(f"  JURISDICTION  : {overview.get('jurisdiction', 'Not specified')}")
    lines.append(f"  DURATION      : {overview.get('contract_duration', 'Not specified')}")
    lines.append(f"  PAGES         : {overview.get('total_pages', 'Unknown')}")
    
    dates = overview.get("dates_mentioned", [])
    if dates:
        lines.append(f"  KEY DATES     : {', '.join(dates[:5])}")
    lines.append("")
    
    # ── TOP RISKS ─────────────────────────────────────────────────────────────
    
    lines.append(divider("-"))
    lines.append("TOP RISKS IDENTIFIED")
    lines.append(divider("-"))
    
    top_risks   = complete_report.get("top_risks", {})
    unique_risks = top_risks.get("unique_risk_types", [])
    
    if unique_risks:
        for i, risk in enumerate(unique_risks, 1):
            lines.append(f"  {i}. [{risk.get('risk_level', '?')}] {risk.get('risk_type', '?')}")
            lines.append(f"     {risk.get('description', '')}")
            lines.append(f"     ACTION: {risk.get('suggestion', '')}")
            lines.append("")
    else:
        lines.append("  No significant risks detected.")
        lines.append("")
    
    # ── RECOMMENDATIONS ───────────────────────────────────────────────────────
    
    lines.append(divider("-"))
    lines.append("RECOMMENDATIONS (IN PRIORITY ORDER)")
    lines.append(divider("-"))
    
    recommendations = complete_report.get("recommendations", [])
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            lines.append(
                f"  {i}. [{rec.get('priority', '?')}] "
                f"{rec.get('related_clause', '')} Clause"
            )
            lines.append(f"     {rec.get('action', '')}")
            lines.append("")
    else:
        lines.append("  No specific recommendations — contract appears acceptable.")
        lines.append("")
    
    # ── FOOTER ────────────────────────────────────────────────────────────────
    
    lines.append(divider())
    lines.append("END OF REPORT — LegalTech NLP Engine v1.0")
    lines.append("DISCLAIMER: This is an automated analysis.")
    lines.append("Always consult a qualified lawyer before signing.")
    lines.append(divider())
    
    return "\n".join(lines)