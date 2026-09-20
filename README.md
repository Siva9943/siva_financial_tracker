# FinTrack — Smart Personal Expense, Budget & Loan Management System

A personal finance platform for tracking income, expenses, loans, interest,
repayment planning, budgets, analytics, and reminders.

## Tech Stack

- **Backend:** Python, Django, Django REST Framework, PostgreSQL, SimpleJWT, Celery, Redis
- **Frontend:** React, Vite, Tailwind CSS, React Router, Axios, Recharts, React Hook Form

## Project Structure

```
Backend/
  manage.py
  Money/                # Django project config
    settings/            # base.py, development.py, production.py
    urls.py, wsgi.py, asgi.py
  apps/                  # Django apps (accounts, transactions, loans, ...)
    core/                # shared utilities (e.g. DRF exception handler)
  services/              # deterministic financial calculation services
  requirements.txt
  .env.example

Frontend/money_tracker/
  src/
    api/                 # Axios client
    routes/              # React Router setup
    layouts/, pages/      # UI shell
  package.json
```

## Backend Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
copy .env.example .env           # then fill in real values
python manage.py migrate
python manage.py runserver
```

Health check: `GET http://localhost:8000/api/health/`

## Frontend Setup

```bash
cd Frontend/money_tracker
npm install
copy .env.example .env
npm run dev
```

App: `http://localhost:5173`

## Environment Variables

See `Backend/.env.example` and `Frontend/money_tracker/.env.example`.
Never commit `.env` files.

## Development Status

Foundation phase complete: project structure, environment configuration,
Django REST Framework + JWT + CORS wiring, Tailwind/React Router/Axios
frontend shell. Feature modules (auth, transactions, loans, budgets,
analytics, AI assistant, etc.) are implemented incrementally in subsequent
phases.
