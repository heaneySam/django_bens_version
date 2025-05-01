Here’s a quick‐reference “Django manage.py” cheat-sheet organized by task. Drop this into your notes so you’ve always got the right command at your fingertips.

---

## 🛠️ Project Setup & App Creation

| Command                                           | What it does                                                      |
|---------------------------------------------------|-------------------------------------------------------------------|
| `django-admin startproject <projname>`            | Create a new Django project                                      |
| `python manage.py startapp <appname>`             | Create a new Django app inside your project                      |
| `pip install django`                              | Install Django into your venv                                    |

---

## 🚀 Development Server

| Command                                                             | Notes                                                           |
|---------------------------------------------------------------------|-----------------------------------------------------------------|
| `python manage.py runserver`                                        | Run dev server on **127.0.0.1:8000** (auto-reload on file change) |
| `python manage.py runserver 0.0.0.0:8000`                           | Expose on all network interfaces (for VM/containers)           |
| `python manage.py runserver --noreload`                             | Disable auto-reload (handy when debugging threading issues)    |
| `python manage.py shell`                                            | Launch interactive Django shell (imports `settings`, ORM setup) |
. .\.venv\Scripts\Activate.ps1  -- CRITICAL TO RUN THE VENV
---

## 🗄️ Database & Migrations

| Command                                         | What it does                                                        |
|-------------------------------------------------|---------------------------------------------------------------------|
| `python manage.py makemigrations`               | Generate new migrations based on model changes                      |
| `python manage.py migrate`                      | Apply pending migrations to the database                            |
| `python manage.py showmigrations`               | List all migrations and their applied/unapplied status              |
| `python manage.py sqlmigrate <app> <migration>` | Show the SQL for a given migration                                  |
| `python manage.py dbshell`                      | Drop you into the DB’s CLI (psql, sqlite3, etc.)                   |
| `python manage.py flush`                        | Remove all data from the database, return to zero state             |

---

## 🧪 Testing & Debugging

| Command                                         | What it does                                                       |
|-------------------------------------------------|--------------------------------------------------------------------|
| `python manage.py test`                         | Run your full test suite                                           |
| `python manage.py test <appname>`               | Run tests for a specific app                                       |
| `python manage.py test --pattern="*_tests.py"`  | Customize test-file patterns                                       |
| `python manage.py check`                        | Perform system checks without touching the database                |
| `python manage.py validate` (<=Django 1.x)      | Validate your project’s configuration (deprecated in 2+)           |

---

## 🔧 Deployment & Static Files

| Command                                                       | What it does                                                               |
|---------------------------------------------------------------|----------------------------------------------------------------------------|
| `python manage.py collectstatic`                              | Gather all static files into `STATIC_ROOT` for production                  |
| `python manage.py compress` (with django-compressor)          | Build and compress CSS/JS assets                                           |
| `python manage.py makemessages -l <lang>`                     | Extract strings for translation                                            |
| `python manage.py compilemessages`                            | Compile `.po` files into `.mo`                                             |
| `python manage.py migrate --fake <app> <migration>`           | Mark migrations as applied without running them (use with caution)         |

---

## 👤 Admin & Data Fixtures

| Command                                               | What it does                                                    |
|-------------------------------------------------------|-----------------------------------------------------------------|
| `python manage.py createsuperuser`                    | Create an admin user (email/username + password prompt)         |
| `python manage.py loaddata <fixture.json>`            | Load data from a fixture (JSON/YAML/XML)                        |
| `python manage.py dumpdata <app>.<Model> > data.json`  | Export data from the DB into JSON fixture                       |

---

## 🔍 Extras & Tips

- **Custom settings**:  
  ```bash
  DJANGO_SETTINGS_MODULE=mysite.settings.dev \
    python manage.py runserver
  ```
- **Run with gunicorn** (for production):  
  ```bash
  gunicorn mysite.wsgi:application --bind 0.0.0.0:8000
  ```
- **Profiling**:  
  ```bash
  python manage.py runserver --nothreading --noreload
  ```
- **Debug toolbar**: add `debug_toolbar` to `INSTALLED_APPS` and include its URLs for in-page SQL/CPU profiling.

- **Generate Secret Key** :
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
---

Keep this sheet handy, and you’ll breeze through development, testing, data management, and deployment without missing a beat!