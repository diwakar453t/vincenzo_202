# PreSkool ERP

Multi-tenant school ERP SaaS built with React 19, MUI 7, Redux Toolkit, FastAPI, SQLAlchemy 2.0, Alembic, Docker, and PostgreSQL-ready deployment assets for Azure App Service and Vercel.

## Structure

- `preskool-erp/backend`: FastAPI API, auth, tenant-aware models, Alembic, smoke test.
- `preskool-erp/frontend`: React 19 app with role-based routing, dashboard, and CRUD pages.
- `.github/workflows/deploy.yml`: CI and Azure deploy workflow.
- `docker-compose.yml`: local stack for frontend, backend, and Postgres.

## Local Run

Backend:

```bash
cd preskool-erp/backend
python3 -m venv ../../.venv
../../.venv/bin/pip install -r requirements.txt
../../.venv/bin/uvicorn app.main:app --reload
```

Frontend:

```bash
cd preskool-erp/frontend
npm install
npm run dev
```

Default seeded super admin:

- `admin@preskool.com`
- `Admin@1234`

## Notes

- Local defaults use SQLite for quick validation.
- Production should set `DATABASE_URL` and `SYNC_DATABASE_URL` to Azure PostgreSQL.
- Alembic migration enables PostgreSQL RLS when run against Postgres.
