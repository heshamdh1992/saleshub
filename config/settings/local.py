from .base import *
from pathlib import Path

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}