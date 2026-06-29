# Installation Guide — LegalTech Contract Parser

## Prerequisites

Before installing, make sure you have:

| Requirement | Version | Check Command |
|---|---|---|
| Python | 3.11+ | `python --version` |
| PostgreSQL | 15+ | `psql --version` |
| Git | Any | `git --version` |
| Docker (optional) | Latest | `docker --version` |

---

## Step 1: Clone Repository

```bash
git clone https://github.com/Priyanka-p-nayak/legaltech-contract-parser.git
cd legaltech-contract-parser
```

**What this does:**
- `git clone` downloads the entire project from GitHub
- `cd` changes your current directory to the project folder

---

## Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

**What is a virtual environment?**
A virtual environment is an isolated Python installation for your project. It prevents conflicts between different projects' dependencies.

**What this does:**
- `python -m venv venv` creates a new virtual environment named "venv"
- `venv\Scripts\activate` activates it (Windows)
- `source venv/bin/activate` activates it (Mac/Linux)

**How to verify it worked:**
You should see `(venv)` at the start of your terminal prompt:
```
(venv) C:\Users\YourName\legaltech-contract-parser>
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**What this does:**
- `pip` is Python's package manager
- `-r requirements.txt` tells pip to install all packages listed in the file

**What gets installed:**
- Django 4.x (web framework)
- djangorestframework (API framework)
- psycopg2-binary (PostgreSQL adapter)
- python-dotenv (environment variables)
- Pillow (image handling)
- django-cors-headers (cross-origin requests)
- gunicorn (production server)

**How to verify:**
```bash
pip list
```
You should see all the packages listed.

---

## Step 4: Set Up PostgreSQL

### Option A — Using pgAdmin (GUI):

1. Open pgAdmin (installed with PostgreSQL)
2. Connect to your PostgreSQL server
3. Right-click on "Databases" → Create → Database
4. Name it: `legaltech_db`
5. Click Save

### Option B — Using Terminal:

```bash
psql -U postgres
```

This opens the PostgreSQL command line. Then type:

```sql
CREATE DATABASE legaltech_db;
\q
```

**What this does:**
- `psql -U postgres` connects to PostgreSQL as the "postgres" user
- `CREATE DATABASE legaltech_db;` creates a new database
- `\q` quits the PostgreSQL command line

**How to verify:**
```bash
psql -U postgres -l
```
You should see `legaltech_db` in the list.

---

## Step 5: Configure Environment

```bash
# Copy the example file
cp .env.example .env
```

**What is a .env file?**
A `.env` file stores environment variables — configuration values that shouldn't be in your code (like passwords).

**Now open `.env` and fill in:**

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
DB_NAME=legaltech_db
DB_USER=postgres
DB_PASSWORD=your-postgresql-password
DB_HOST=localhost
DB_PORT=5432
```

**What each variable means:**
- `SECRET_KEY` — Django's secret key for security (generate a random string)
- `DEBUG` — Set to `True` for development, `False` for production
- `DB_NAME` — Name of your PostgreSQL database
- `DB_USER` — PostgreSQL username
- `DB_PASSWORD` — PostgreSQL password
- `DB_HOST` — Database server address (localhost for local)
- `DB_PORT` — Database port (5432 is PostgreSQL default)

**⚠️ Important:** Never commit `.env` to GitHub! It's already in `.gitignore`.

---

## Step 6: Run Database Migrations

```bash
python manage.py migrate
```

**What are migrations?**
Migrations are Django's way of creating database tables. When you define models in `models.py`, Django needs to create the actual tables in PostgreSQL.

**What this does:**
- Reads all migration files in `contracts/migrations/`
- Creates the necessary tables in PostgreSQL
- Sets up Django's built-in tables (users, sessions, etc.)

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, contracts, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying contracts.0001_initial... OK
  ...
```

---

## Step 7: Create Admin User

```bash
python manage.py createsuperuser
```

**What this does:**
Creates a user account that can access the Django Admin panel.

**You'll be prompted:**
```
Username: admin
Email address: (press Enter to skip)
Password: admin123
Password (again): admin123
```

**⚠️ Note:** Django will warn you that "admin123" is too common. Type `y` to continue anyway (this is just for development).

---

## Step 8: Start the Server

```bash
python manage.py runserver
```

**What this does:**
Starts Django's development server on port 8000.

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 4.2.0, using settings 'legaltech_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## Step 9: Verify Installation

Open your browser and check these URLs:

| URL | Expected Result |
|---|---|
| `http://127.0.0.1:8000/api/v1/health/` | JSON with `"status": "healthy"` |
| `http://127.0.0.1:8000/admin/` | Admin login page |
| `http://127.0.0.1:8000/admin/stats/` | Statistics dashboard |

**Test the API:**
```bash
# In a new terminal (keep the server running)
curl http://127.0.0.1:8000/api/v1/health/
```

**Expected response:**
```json
{
    "success": true,
    "message": "LegalTech API is running successfully.",
    "data": {
        "api_version": "1.0.0",
        "status": "healthy"
    }
}
```

---

## Troubleshooting

### Error: `could not connect to server`

**Problem:** PostgreSQL is not running.

**Fix:**
```bash
# Windows: Start PostgreSQL service
# Open Services (services.msc) and start "postgresql-x64-15"

# Mac:
brew services start postgresql

# Linux:
sudo service postgresql start
```

---

### Error: `ModuleNotFoundError: No module named 'django'`

**Problem:** Virtual environment not activated.

**Fix:**
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Then reinstall:
```bash
pip install -r requirements.txt
```

---

### Error: `relation "contracts_document" does not exist`

**Problem:** Migrations not run.

**Fix:**
```bash
python manage.py migrate
```

---

### Error: `Invalid HTTP_HOST header`

**Problem:** Django's security settings blocking the request.

**Fix:** Open `legaltech_project/settings.py` and find:
```python
ALLOWED_HOSTS = []
```

Change to:
```python
ALLOWED_HOSTS = ['*']
```

**⚠️ Note:** Only use `['*']` in development. For production, specify exact domains.

---

### Error: `permission denied for database`

**Problem:** PostgreSQL user doesn't have permission.

**Fix:**
```bash
psql -U postgres
```

Then run:
```sql
GRANT ALL PRIVILEGES ON DATABASE legaltech_db TO postgres;
\q
```

---

## Next Steps

After successful installation:

1. **Test the API** — See `docs/API_DOCUMENTATION.md`
2. **Explore the Admin** — Login at `/admin/`
3. **Run tests** — `python manage.py test`
4. **Read the code** — Start with `contracts/models.py`

---

## Need Help?

- Check `README.md` for project overview
- Check `docs/PROJECT_STRUCTURE.md` for folder explanations
- Check `docs/API_DOCUMENTATION.md` for API details