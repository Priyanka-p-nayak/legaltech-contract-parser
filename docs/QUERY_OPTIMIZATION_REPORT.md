# Query Optimization Report — 
**Goal:** Eliminate N+1 query patterns on the heaviest endpoints.

---

## What is an N+1 Query Problem?

An N+1 problem happens when fetching a list of N items requires
1 query to get the list, plus N more queries (one per item) to get
related data — instead of fetching everything in 2-3 total queries.

```python
# ❌ N+1 pattern (BAD)
documents = Document.objects.all()        # 1 query
for doc in documents:
    doc.clauses.count()                     # +1 query EACH time
    doc.risk_flags.count()                  # +1 query EACH time
# For 20 documents: 1 + 20 + 20 = 41 queries

# ✅ Optimized (GOOD)
documents = Document.objects.prefetch_related('clauses', 'risk_flags')
for doc in documents:
    doc.clauses.count()                     # 0 extra queries — cached
    doc.risk_flags.count()                  # 0 extra queries — cached
# For 20 documents: still just ~3 queries total