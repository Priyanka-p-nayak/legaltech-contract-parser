# contracts/services/clause_categorizer.py

# WHY THIS FILE EXISTS:
# Legal contracts have standard clause types.
# This file reads each clause and assigns it a category.
# Example:
#   Clause: "Party A shall indemnify and hold harmless Party B..."
#   Category: "INDEMNIFICATION"
#
# We build a keyword dictionary where each category has
# a list of words that typically appear in that type of clause.
# The clause with the most matching keywords wins that category.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

import re
import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── CATEGORY KEYWORD DICTIONARY ───────────────────────────────────────────────

# This is the most important data structure in this file.
# Keys = category names (what we will label the clause)
# Values = list of keywords that strongly suggest that category
#
# How scoring works:
#   We count how many keywords from each category appear in a clause.
#   The category with the highest count wins.
#   If no keywords match, the category is "GENERAL".

CLAUSE_CATEGORIES = {

    "DEFINITIONS": [
        "means", "defined", "definition", "refers to",
        "hereinafter", "shall mean", "is defined as",
        "the term", "for purposes of this agreement"
    ],

    "PAYMENT_TERMS": [
        "payment", "invoice", "fee", "fees", "pay", "paid",
        "amount", "price", "cost", "billing", "remuneration",
        "compensation", "due date", "overdue", "installment",
        "advance", "deposit", "refund", "currency"
    ],

    "INDEMNIFICATION": [
        "indemnify", "indemnification", "indemnitor", "indemnitee",
        "hold harmless", "defend", "indemnified party",
        "losses", "damages", "claims", "liabilities",
        "third party claims", "legal costs", "attorney fees"
    ],

    "TERMINATION": [
        "terminate", "termination", "end", "expiry", "expiration",
        "cancellation", "cancel", "notice of termination",
        "upon termination", "effective date of termination",
        "right to terminate", "immediate termination",
        "without cause", "for cause", "material breach"
    ],

    "CONFIDENTIALITY": [
        "confidential", "confidentiality", "non-disclosure",
        "proprietary", "trade secret", "secret", "disclose",
        "disclosure", "nda", "restricted information",
        "classified", "private information", "keep confidential"
    ],

    "INTELLECTUAL_PROPERTY": [
        "intellectual property", "ip", "copyright", "patent",
        "trademark", "trade mark", "license", "ownership",
        "proprietary rights", "work product", "inventions",
        "moral rights", "assignment of rights"
    ],

    "LIABILITY": [
        "liability", "liable", "limitation of liability",
        "indirect damages", "consequential damages",
        "special damages", "punitive damages",
        "total liability", "maximum liability",
        "shall not be liable", "not responsible"
    ],

    "DISPUTE_RESOLUTION": [
        "dispute", "arbitration", "arbitrator", "mediation",
        "mediator", "litigation", "court", "jurisdiction",
        "resolve", "resolution", "settlement", "governing law",
        "legal proceedings", "claim", "controversy"
    ],

    "FORCE_MAJEURE": [
        "force majeure", "act of god", "unforeseen",
        "circumstances beyond", "natural disaster",
        "earthquake", "flood", "war", "riot",
        "pandemic", "epidemic", "government action",
        "beyond control", "unforeseeable"
    ],

    "WARRANTIES": [
        "warrant", "warranty", "warranties", "representation",
        "represents", "guarantee", "as is", "no warranty",
        "disclaimer", "fitness for purpose", "merchantability",
        "satisfactory quality", "free from defects"
    ],

    "PENALTIES": [
        "penalty", "penalties", "liquidated damages",
        "late payment", "interest rate", "surcharge",
        "fine", "breach penalty", "default interest",
        "compensation for delay", "forfeit"
    ],

    "EXCLUSIVITY": [
        "exclusive", "exclusivity", "sole", "non-exclusive",
        "exclusively", "only supplier", "preferred supplier",
        "not to engage", "restricted from",
        "sole and exclusive", "exclusive rights"
    ],

    "GOVERNING_LAW": [
        "governing law", "governed by", "applicable law",
        "laws of", "legal jurisdiction", "choice of law",
        "subject to the laws", "under the laws of"
    ],

    "ASSIGNMENT": [
        "assignment", "assign", "assignee", "assignor",
        "transfer", "novation", "delegate",
        "cannot be assigned", "may not assign",
        "prior written consent", "permitted assigns"
    ],

    "NOTICE": [
        "notice", "notification", "notify", "written notice",
        "days notice", "notice period", "email notice",
        "address for notice", "effective notice",
        "receipt of notice", "delivery of notice"
    ],
}

# ── FUNCTION 1: CATEGORIZE A SINGLE CLAUSE ───────────────────────────────────

def categorize_clause(clause_text):
    """
    Assign a category to a single clause based on keyword matching.

    Arguments:
        clause_text (str): The text of one clause

    Returns:
        dict: Contains category name and confidence score
        Example: {"category": "INDEMNIFICATION", "score": 5, "matched_keywords": [...]}
    """

    if not clause_text:
        return {"category": "GENERAL", "score": 0, "matched_keywords": []}

    # Convert to lowercase for case-insensitive matching
    # We keep the original for display but match against lowercase
    text_lower = clause_text.lower()

    # Dictionary to store scores for each category
    # We will count how many keywords from each category appear in the clause
    category_scores = {}

    # Also track which keywords matched (useful for debugging and viva)
    category_keywords_matched = {}

    # ── SCORING LOOP ──────────────────────────────────────────────────────────

    for category_name, keywords in CLAUSE_CATEGORIES.items():

        score = 0
        matched = []

        for keyword in keywords:
            # Check if keyword appears in the clause text
            # We use 'in' for simple substring matching
            if keyword.lower() in text_lower:
                score += 1
                matched.append(keyword)

        category_scores[category_name] = score
        category_keywords_matched[category_name] = matched

    # ── FIND WINNING CATEGORY ─────────────────────────────────────────────────

    # max() with key= finds the category with the highest score
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]

    # If the best score is 0, no keywords matched — call it GENERAL
    if best_score == 0:
        return {
            "category": "GENERAL",
            "score": 0,
            "matched_keywords": []
        }

    return {
        "category": best_category,
        "score": best_score,
        "matched_keywords": category_keywords_matched[best_category]
    }


# ── FUNCTION 2: CATEGORIZE ALL CLAUSES ───────────────────────────────────────

def categorize_all_clauses(clauses):
    """
    Categorize every clause in the contract.

    Takes the list of clauses from text_cleaner.split_into_clauses()
    and adds a category to each one.

    Arguments:
        clauses (list of dict): Output from split_into_clauses()
        Each item has: {"heading": "...", "content": "..."}

    Returns:
        list of dict: Same list but with category added
        Each item has: {"heading": "...", "content": "...", "category": "...", "score": N}
    """

    if not clauses:
        logger.warning("No clauses received for categorization")
        return []

    categorized = []

    for clause in clauses:

        # Get the content of this clause
        content = clause.get("content", "")
        heading = clause.get("heading", "")

        # Combine heading and content for better keyword matching
        # The heading often gives a strong hint about the category
        combined_text = f"{heading} {content}"

        # Run categorization
        result = categorize_clause(combined_text)

        # Add category info to the clause dict
        categorized_clause = {
            "heading":          heading,
            "content":          content,
            "category":         result["category"],
            "category_score":   result["score"],
            "matched_keywords": result["matched_keywords"]
        }

        categorized.append(categorized_clause)
        logger.debug(
            f"Clause '{heading[:30]}' → {result['category']} "
            f"(score: {result['score']})"
        )

    logger.info(f"Categorized {len(categorized)} clauses")
    return categorized


# ── FUNCTION 3: SUMMARIZE CATEGORIES ─────────────────────────────────────────

def get_category_summary(categorized_clauses):
    """
    Create a summary showing how many clauses of each category exist.

    Useful for the dashboard — Member 3 will display this as a chart.

    Arguments:
        categorized_clauses (list): Output from categorize_all_clauses()

    Returns:
        dict: Category name → count
        Example: {"INDEMNIFICATION": 2, "PAYMENT_TERMS": 3, "GENERAL": 1}
    """

    summary = {}

    for clause in categorized_clauses:
        category = clause.get("category", "GENERAL")

        # If this category is seen for the first time, start count at 0
        if category not in summary:
            summary[category] = 0

        summary[category] += 1

    return summary