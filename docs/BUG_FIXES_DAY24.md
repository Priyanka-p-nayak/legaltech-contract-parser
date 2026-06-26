# Integration Bug Fixes — Day 24

This document records 7 integration-level bugs found
during a full cross-module audit and the fixes applied.

These are NOT crash bugs — the app worked fine before.
These are **consistency bugs**: places where two or more
parts of the system disagreed with each other in ways
that would confuse Member 2 or Member 3, or crash their
frontend code unexpectedly.

---

## Bug 1 — Duplicate clause/risk counting logic

**Problem:** `total_clauses` / `total_risks` were calculated
independently in `DocumentListSerializer` and
`DocumentDetailSerializer`, using raw `.count()` calls.

**Fix:** Added `total_clauses_count` and `total_risks_count`
properties on the `Document` model as the single source
of truth. Both serializers now call these properties.

**Files:** `contracts/models.py`, `contracts/serializers.py`

---

## Bug 2 — Dashboard duplicated the same counting logic again

**Problem:** `DashboardOverviewView` had its OWN third copy
of `doc.clauses.count()` / `doc.risk_flags.count()`.

**Fix:** Updated to use `doc.total_clauses_count` /
`doc.total_risks_count`, same as Bug 1.

**Files:** `contracts/views.py`

---

## Bug 3 — `risks_by_severity` omits zero-count severities

**Problem:** `StatsView` used Django's `.values().annotate()`
which only returns rows that actually exist in the database.
If there were zero `low` severity risks, the `low` key was
**completely missing** from the response.

**Fix:** `StatsView` now always returns exactly 3 entries
(high, medium, low), defaulting missing ones to count 0.

**Files:** `contracts/views.py`

---

## Bug 4 — Same omission bug for `documents_by_status`

**Problem:** Identical issue as Bug 3, for document statuses.

**Fix:** Same pattern applied — always returns all 4 statuses.

**Files:** `contracts/views.py`

---

## Bug 5 — NLP process endpoint had no bulk size limit

**Problem:** `/clauses/` and `/risks/` endpoints reject lists
over 100 items. But `/nlp/documents/{id}/process/`
accepted unlimited clauses and risk_flags.

**Fix:** Added the same 100-item limit check to
`NLPProcessResultView.post`.

**Files:** `contracts/nlp_views.py`

---

## Bug 6 — Invalid `?ordering=` silently ignored

**Problem:** Sending an invalid `ordering` value fell back to
the default silently with no feedback.

**Fix:** Response now includes a `warning` field explaining
the value was invalid and listing allowed values.

**Files:** `contracts/views.py`

---

## Bug 7 — Invalid `?severity=` filter silently returned zero results

**Problem:** Unlike the `status` filter on document list, the
`severity` filter on `/risks/` GET silently filtered to an
empty list for typos.

**Fix:** Invalid severity values are now ignored (all risks
returned) with a `warning` field explaining what happened.

**Files:** `contracts/views.py`

---

## Test Coverage Added

All 7 bugs now have dedicated regression tests in
`contracts/tests/test_integration_bugfixes.py` (25 tests).
