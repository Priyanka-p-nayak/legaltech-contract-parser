# Security Documentation — LegalTech Backend

**Maintained by:** Member 1 — Backend, Database & APIs

---

## Overview

This document explains the security decisions made in
`legaltech_project/settings.py` and the security
controls built into the API itself.

---

## Security Check Command

Run at any time to audit current settings:

```bash
python manage.py security_check