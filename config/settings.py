"""Local Windows settings plus an isolated Vercel/Neon demo mode."""
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.environ.get("VERCEL") == "1"
RUMI_DEMO_MODE = IS_VERCEL
RUMI_ATTACHMENTS_ENABLED = not IS_VERCEL

if IS_VERCEL:
    # Vercel's filesystem is temporary. Only transient runtime scratch files go here.
    DATA_DIR = Path(os.environ.get("RUMI_DATA_DIR", "/tmp/rumi-dental-demo")).resolve()
else:
    DATA_DIR = Path(os.environ.get("RUMI_DATA_DIR", BASE_DIR / "runtime" / "development")).resolve()

if not IS_VERCEL and (DATA_DIR.parent / ("." + DATA_DIR.name + ".rumi-restore.json")).exists():
    raise RuntimeError("Interrupted restore: run scripts/recovery.py repair with this explicit --data-dir before startup. Nothing initialized.")

DATA_DIR.mkdir(parents=True, exist_ok=True)

if IS_VERCEL:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
    if len(SECRET_KEY) < 50:
        raise RuntimeError("Set DJANGO_SECRET_KEY in Vercel Environment Variables (use a newly generated secret of at least 50 characters).")
else:
    key_file = DATA_DIR / "secret.key"
    try:
        with key_file.open("x", encoding="utf-8") as handle:
            handle.write(get_random_secret_key())
    except FileExistsError:
        pass
    SECRET_KEY = key_file.read_text(encoding="utf-8").strip()

DEBUG = False

if IS_VERCEL:
    allowed = {".vercel.app"}
    vercel_host = os.environ.get("VERCEL_URL", "").strip()
    if vercel_host:
        allowed.add(vercel_host.split("/")[0])
    allowed.update(host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip())
    ALLOWED_HOSTS = sorted(allowed)
    CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]
    CSRF_TRUSTED_ORIGINS += [
        "https://" + host.lstrip(".")
        for host in ALLOWED_HOSTS
        if host != ".vercel.app" and host not in ("localhost", "127.0.0.1")
    ]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
    CSRF_TRUSTED_ORIGINS = []

INSTALLED_APPS = [
    "clinic",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "clinic.middleware.PrivacyMiddleware",
    "clinic.backups.locks.RuntimeBoundaryMiddleware",
    "clinic.middleware.ClinicSessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if IS_VERCEL:
    # File locks are local to one serverless instance and cannot coordinate Vercel instances.
    MIDDLEWARE.remove("clinic.backups.locks.RuntimeBoundaryMiddleware")

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "clinic.context_processors.deployment_flags",
        ]
    },
}]
WSGI_APPLICATION = "config.wsgi.application"

if IS_VERCEL:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    parsed_database_url = urlparse(database_url)
    if parsed_database_url.scheme not in ("postgres", "postgresql") or not parsed_database_url.hostname or not parsed_database_url.path.strip("/"):
        raise RuntimeError("Set DATABASE_URL to the Neon PostgreSQL connection string in Vercel Environment Variables.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed_database_url.path.lstrip("/")),
            "USER": unquote(parsed_database_url.username or ""),
            "PASSWORD": unquote(parsed_database_url.password or ""),
            "HOST": parsed_database_url.hostname,
            "PORT": parsed_database_url.port or 5432,
            "OPTIONS": {"sslmode": "require"},
            "CONN_MAX_AGE": 0,
            "DISABLE_SERVER_SIDE_CURSORS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DATA_DIR / "clinic.sqlite3",
            "OPTIONS": {"timeout": 20},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Asia/Karachi"
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SECURE = IS_VERCEL
CSRF_COOKIE_SECURE = IS_VERCEL
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = IS_VERCEL
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if IS_VERCEL:
    SECURE_HSTS_SECONDS = 3600

# Never use Django's verbose request formatting: only allowlisted diagnostics.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"safe": {"class": "clinic.diagnostics.SafeDiagnosticHandler", "level": "WARNING"}},
    "loggers": {
        name: {"handlers": ["safe"], "level": "WARNING", "propagate": False}
        for name in ["django.server", "django.request", "django.security"]
    },
}
LOGGING["handlers"]["null"] = {"class": "logging.NullHandler"}
for decoder in ["pypdf", "PIL"]:
    LOGGING["loggers"][decoder] = {"handlers": ["null"], "propagate": False}

RUMI_MAX_UPLOAD_BYTES = int(os.environ.get("RUMI_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
RUMI_MAX_IMAGE_SIDE = int(os.environ.get("RUMI_MAX_IMAGE_SIDE", 10000))
RUMI_MAX_IMAGE_PIXELS = int(os.environ.get("RUMI_MAX_IMAGE_PIXELS", 25000000))
RUMI_MAX_PDF_PAGES = int(os.environ.get("RUMI_MAX_PDF_PAGES", 200))
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_TEMP_DIR = DATA_DIR / "upload-tmp"
FILE_UPLOAD_TEMP_DIR.mkdir(exist_ok=True)

# Portable local runtime settings are deliberately not loaded in the cloud demo.
portable_file = DATA_DIR / "portable.json"
if not IS_VERCEL and portable_file.is_file():
    from clinic.backups.archive import read_json, validate_portable
    portable = read_json(portable_file, 65536)
    validate_portable(portable)
    for portable_name, portable_value in portable["limits"].items():
        if portable_name not in os.environ:
            globals()[portable_name] = portable_value
