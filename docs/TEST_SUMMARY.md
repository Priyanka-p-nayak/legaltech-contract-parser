# Test Suite Summary — Final

**Date:** July 7, 2026  
**Built by:** Member 1 — Backend, Database & APIs

---

## How to Run

```bash
# Full suite
python manage.py test contracts.tests integration --verbosity=1

# One group only
python manage.py test contracts.tests.test_final --verbosity=2

# With timing
python manage.py test contracts.tests integration --verbosity=2 --timing