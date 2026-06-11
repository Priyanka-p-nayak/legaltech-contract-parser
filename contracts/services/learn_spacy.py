# contracts/services/learn_spacy.py

# WHY THIS FILE EXISTS:
# This is a LEARNING file for Week 2.
# We practice spaCy here before writing production code.
# Delete this file before final submission.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# spacy is the main NLP library
import spacy

# ── LOAD THE LANGUAGE MODEL ───────────────────────────────────────────────────

# en_core_web_sm is the small English language model we downloaded earlier
# "sm" = small (fast but less accurate)
# "md" = medium (balanced)
# "lg" = large (slow but most accurate)
# For this project, "sm" is fine
nlp = spacy.load("en_core_web_sm")


def explore_spacy_entities():
    """
    Practice finding named entities using spaCy.
    
    Named Entity Recognition (NER) finds:
    ORG   = Organizations / Companies
    DATE  = Dates
    GPE   = Countries, cities, states (Geo-Political Entities)
    PERSON = People's names
    MONEY  = Money amounts
    LAW    = Legal references
    """

    # Sample contract text for practice
    sample_text = """
    This Service Agreement is entered into between Tata Consultancy Services Limited,
    a company incorporated under the laws of India, having its registered office at
    Mumbai, Maharashtra (hereinafter referred to as "Service Provider") and
    Reliance Industries Limited, registered in New Delhi, India
    (hereinafter referred to as "Client").

    This Agreement shall commence on January 1, 2024 and shall remain in force
    until December 31, 2025, unless terminated earlier in accordance with
    Clause 9 of this Agreement.

    The governing law of this Agreement shall be the laws of India,
    and any disputes shall be resolved in the courts of Mumbai.

    The total contract value is INR 50,00,000 (Fifty Lakhs).
    """

    # ── STEP 1: PROCESS THE TEXT ───────────────────────────────────────────────

    # nlp() runs the full NLP pipeline on the text
    # It returns a Doc object containing all analysis results
    doc = nlp(sample_text)

    # ── STEP 2: EXPLORE ENTITIES ───────────────────────────────────────────────

    print("=" * 60)
    print("ALL NAMED ENTITIES FOUND:")
    print("=" * 60)

    # doc.ents is a list of all named entities found in the text
    # Each entity has:
    #   .text  = the actual text (e.g. "Tata Consultancy Services")
    #   .label_ = the entity type (e.g. "ORG", "DATE", "GPE")
    #   .start_char = position where the entity starts in the text
    #   .end_char   = position where the entity ends
    for entity in doc.ents:
        print(f"  Text: '{entity.text}'")
        print(f"  Type: {entity.label_}")
        print(f"  Explanation: {spacy.explain(entity.label_)}")
        print()

    # ── STEP 3: FILTER BY ENTITY TYPE ─────────────────────────────────────────

    print("=" * 60)
    print("ORGANIZATIONS ONLY (ORG):")
    print("=" * 60)

    # Filter entities to only show ORG type
    organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    for org in organizations:
        print(f"  - {org}")

    print("\n" + "=" * 60)
    print("DATES ONLY (DATE):")
    print("=" * 60)

    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    for date in dates:
        print(f"  - {date}")

    print("\n" + "=" * 60)
    print("LOCATIONS (GPE):")
    print("=" * 60)

    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    for loc in locations:
        print(f"  - {loc}")

    # ── STEP 4: EXPLORE TOKENS ─────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("FIRST 10 TOKENS (individual words):")
    print("=" * 60)

    # doc itself is iterable — each item is a Token
    # Token properties:
    #   .text       = the word itself
    #   .pos_       = part of speech (NOUN, VERB, ADJ...)
    #   .is_stop    = True if it's a stop word (the, a, is, are...)
    #   .lemma_     = base form (running → run, companies → company)
    for token in list(doc)[:10]:
        print(f"  Word: '{token.text}'")
        print(f"    POS: {token.pos_}")
        print(f"    Lemma: {token.lemma_}")
        print(f"    Is stop word: {token.is_stop}")
        print()

    # ── STEP 5: EXPLORE SENTENCES ─────────────────────────────────────────────

    print("=" * 60)
    print("SENTENCES FOUND:")
    print("=" * 60)

    # doc.sents splits the text into sentences
    for i, sentence in enumerate(doc.sents):
        print(f"  Sentence {i+1}: {sentence.text[:80]}...")


def explore_spacy_matcher():
    """
    Practice using spaCy's Matcher for custom pattern matching.
    
    Matcher lets us find custom patterns that NER might miss.
    Example: finding "governed by the laws of [COUNTRY]"
    """

    # We need Matcher from spacy.matcher
    from spacy.matcher import Matcher

    # Create a Matcher object linked to our vocabulary
    matcher = Matcher(nlp.vocab)

    # ── DEFINE A CUSTOM PATTERN ────────────────────────────────────────────────

    # Pattern: find "laws of" followed by any proper noun
    # Each dict in the list matches one token
    # "LOWER" means match the lowercase version
    # "POS" means match the part-of-speech tag
    jurisdiction_pattern = [
        {"LOWER": "laws"},          # word "laws"
        {"LOWER": "of"},            # word "of"
        {"POS": "PROPN"}            # any proper noun (India, England, etc.)
    ]

    # Add pattern to matcher with a name
    matcher.add("JURISDICTION_PATTERN", [jurisdiction_pattern])

    # Sample text
    text = "This agreement is governed by the laws of India and any disputes will be resolved in England."

    # Process the text
    doc = nlp(text)

    # Run the matcher on the doc
    # matches returns list of (match_id, start, end) tuples
    matches = matcher(doc)

    print("=" * 60)
    print("CUSTOM PATTERN MATCHES (jurisdiction):")
    print("=" * 60)

    for match_id, start, end in matches:
        # doc[start:end] gives us the matched span of tokens
        matched_span = doc[start:end]
        print(f"  Found: '{matched_span.text}'")
        print(f"  Last word (jurisdiction): '{doc[end-1].text}'")


# Run both practice functions
if __name__ == "__main__":
    print("\n📌 EXPLORING NAMED ENTITY RECOGNITION\n")
    explore_spacy_entities()

    print("\n\n📌 EXPLORING CUSTOM PATTERN MATCHING\n")
    explore_spacy_matcher()