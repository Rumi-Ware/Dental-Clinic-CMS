# Temporary Vercel + Neon interface demo

This deployment mode exists only to preview the Django interface online with fictional records. It is not approved for real clinic use.

## Platform behavior

- Vercel detects this Django project from `manage.py` and `config.wsgi.application`; no custom API wrapper or `vercel.json` is required for the current Django integration.
- Python is pinned to 3.13 in `.python-version`.
- When Vercel sets `VERCEL=1`, Django uses Neon PostgreSQL from `DATABASE_URL`, requires `DJANGO_SECRET_KEY`, and uses Vercel's `VERCEL_URL` plus `ALLOWED_HOSTS` for host validation.
- Local Windows development continues to use the existing SQLite database and local secret file.
- Static assets are collected from `STATIC_ROOT` and served using WhiteNoise/Vercel static asset handling.
- Attachment uploads and local backup endpoints are disabled in demo mode. Vercel's local filesystem is temporary and cannot be used as permanent attachment or backup storage.
- The local runtime boundary file lock is not used in demo mode because a lock on one serverless instance cannot coordinate other instances.

## Vercel environment variables

Set these for Preview and Production as needed:

- `DJANGO_SECRET_KEY`: a newly generated random Django secret key (keep private).
- `DATABASE_URL`: the Neon pooled PostgreSQL connection string.
- `ALLOWED_HOSTS`: optional comma-separated custom hostnames. The `.vercel.app` domain is allowed by default.

Do not commit these values or place them in source code.

## First-time Neon setup

After connecting Vercel to Neon and setting the environment variables, run migrations against the Neon database from a trusted local terminal:

PowerShell:

```powershell
$env:VERCEL = "1"
$env:DJANGO_SECRET_KEY = "paste-your-generated-secret-here"
$env:DATABASE_URL = "paste-your-Neon-pooled-connection-string-here"
python manage.py migrate
python manage.py createsuperuser
```

Use a unique demo Owner account and fictional data only. Do not use the local SQLite database or copy existing clinic records into Neon.

After migrations and account creation, remove the temporary `VERCEL`, `DJANGO_SECRET_KEY`, and `DATABASE_URL` values from that PowerShell session with `Remove-Item Env:VERCEL, Env:DJANGO_SECRET_KEY, Env:DATABASE_URL`.

## Explicit limitations

This mode is a visual/learning demo. It does not provide durable uploads, cloud backups, background backup scheduling, multi-instance file locks, clinical operational readiness, or production approval. Never enter real patient information.
