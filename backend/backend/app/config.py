"""Application settings.

Values come from environment variables or from a .env file. The .env file is
looked for in this order:
  1. the path in the HANKS_ENV_FILE environment variable
  2. ~/hanks-secrets/hanks.env      (recommended: outside the project folder)
  3. backend/.env                   (fallback for local development)

The app REFUSES TO START if the JWT secret or CORS setting is unsafe.
"""
import hashlib
import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path:
    explicit = os.environ.get("HANKS_ENV_FILE")
    if explicit:
        return Path(explicit).expanduser()
    outside = Path.home() / "hanks-secrets" / "hanks.env"
    if outside.is_file():
        return outside
    return Path(__file__).resolve().parents[1] / ".env"


ENV_FILE = _find_env_file()

# The static website folder (holds index.html, css/, js/, img/) -- the project
# root, two levels above this file. Uploaded product images are saved under it.
UI_DIR = Path(__file__).resolve().parents[2]

# SHA-256 fingerprints of JWT secrets that were exposed and must never be used
# again. (Only the hash is stored, so this file does not leak the old secret.)
_LEAKED_SECRET_HASHES = {
    "3bcd641d715c0911e660a10091d21161b8ad7559cf0580f0f8690a46b8de8121",
}
_PLACEHOLDER_WORDS = ("change-me", "changeme", "change_me", "please-use", "your-secret", "placeholder", "example")
_GENERATE_HINT = 'python -c "import secrets; print(secrets.token_urlsafe(48))"'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hanks_bbq"

    # Auth -- jwt_secret has NO default on purpose: the app must not start without one.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Server
    app_port: int = 8000
    # Comma separated browser origins allowed to call the API from ANOTHER site.
    # Empty (the default) = same-origin only, which is what you want because the
    # app serves the website itself. "*" is rejected.
    cors_origins: str = ""
    # /docs and /openapi.json are hidden unless you set DOCS_ENABLED=true.
    docs_enabled: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _check_security(self) -> "Settings":
        secret = (self.jwt_secret or "").strip()
        if not secret:
            raise ValueError(f"JWT_SECRET is missing. Generate one with:  {_GENERATE_HINT}")
        if len(secret) < 32:
            raise ValueError(f"JWT_SECRET is too short (need 32+ characters). Generate one with:  {_GENERATE_HINT}")
        if any(w in secret.lower() for w in _PLACEHOLDER_WORDS):
            raise ValueError(f"JWT_SECRET is still a placeholder. Generate a real one with:  {_GENERATE_HINT}")
        if len(set(secret)) < 10:
            raise ValueError(f"JWT_SECRET is too repetitive. Generate one with:  {_GENERATE_HINT}")
        if hashlib.sha256(secret.encode()).hexdigest() in _LEAKED_SECRET_HASHES:
            raise ValueError(f"JWT_SECRET is a secret that was leaked. Generate a NEW one with:  {_GENERATE_HINT}")
        if self.jwt_algorithm not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM must be HS256, HS384 or HS512.")
        if any(o == "*" for o in self.cors_origin_list):
            raise ValueError("CORS_ORIGINS=* is not allowed. Leave it empty (same-origin) or list your real site, e.g. https://yourdomain.com")
        return self


settings = Settings()
