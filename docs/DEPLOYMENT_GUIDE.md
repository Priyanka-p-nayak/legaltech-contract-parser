# Deployment Guide — LegalTech Contract Parser

## Production Checklist

Before deploying to production, verify:

- [ ] `DEBUG=False` in environment
- [ ] `SECRET_KEY` is a long random string (50+ characters)
- [ ] Database password is strong and not 'postgres123'
- [ ] `ALLOWED_HOSTS` set to real domain (e.g., `api.legaltech.com`)
- [ ] `CORS_ALLOWED_ORIGINS` set to real frontend domain
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] All migrations applied: `python manage.py migrate`
- [ ] Admin superuser created
- [ ] Docker images built and tested

---

## Environment Variables for Production

Create a secure `.env` file on your production server:

```env
SECRET_KEY=VkjdGyOqb4wtnXlDoFh590ooK1VRyUATcx8S_v0-y90LIMPCLL6YoyZ9yfwl2y1RuTc
DEBUG=False
DB_NAME=legaltech_production
DB_USER=legaltech_user
DB_PASSWORD=very-strong-password-here
DB_HOST=your-database-host
DB_PORT=5432
ALLOWED_HOST=your-domain.com
FRONTEND_URL=https://your-frontend.com