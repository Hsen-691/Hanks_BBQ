"""Security checks. Run from backend/:   python -m pytest tests -q"""
import base64, hashlib, importlib, io, json, os, subprocess, sys, tempfile, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

GOOD_SECRET = "Zk3-pQ9vLx7_Tn2mWb8YrC4dHf6JgE1sUa5oNiKqVtX0wMyB"
os.environ["JWT_SECRET"] = GOOD_SECRET
os.environ["CORS_ORIGINS"] = ""
os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mkdtemp() + "/t.db"
os.environ["HANKS_ENV_FILE"] = "/nonexistent.env"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import UI_DIR, app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402

Base.metadata.create_all(engine)
client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- static files
@pytest.mark.parametrize("path", [
    "/backend/.env", "/.env", "/backend/backups/hanks_bbq_20261022_110411.dump",
    "/backend/app/main.py", "/backend/app/config.py", "/README.md", "/.DS_Store",
    "/venv/pyvenv.cfg", "/backend/.venv/pyvenv.cfg", "/css/../backend/.env",
    "/css/%2e%2e/backend/.env", "/img/../backend/.env", "/js/..%2f..%2fbackend%2f.env",
    "/css/.DS_Store", "/img/.hidden.png", "/backend/", "/backend", "/js/", "/css/",
    "/%2e%2e/%2e%2e/etc/passwd", "/img/uploads/../../backend/.env",
])
def test_private_files_are_404(path):
    r = client.get(path)
    assert r.status_code in (404, 405, 307), (path, r.status_code)
    assert b"JWT_SECRET" not in r.content and b"PGDMP" not in r.content


def test_site_still_works():
    for p in ["/", "/index.html", "/admin.html", "/privacy.html", "/terms.html", "/reset.html"]:
        assert client.get(p).status_code == 200, p
    assert client.get("/css/shop.css").status_code == 200
    assert client.get("/js/app.js").status_code == 200
    assert client.get("/img/logo.png").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_security_headers_and_csp():
    r = client.get("/")
    h = r.headers
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    csp = h["content-security-policy"]
    assert "frame-ancestors 'none'" in csp and "object-src 'none'" in csp and "'unsafe-inline'" in csp.split("style-src")[1].split(";")[0]
    script_src = [d for d in csp.split(";") if "script-src" in d][0]
    assert "unsafe-inline" not in script_src and "sha256-" in script_src  # inline script allowed by hash only
    # the hash really matches the inline script in index.html
    import re
    inline = re.findall(r"<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>", (ROOT / "index.html").read_text(), re.S)[0]
    assert hashlib.sha256(inline.encode()).digest() == base64.b64decode(re.search(r"sha256-([^']+)", script_src).group(1))
    assert client.get("/health").headers["cache-control"] == "no-store"
    assert "strict-transport-security" in TestClient(app, base_url="https://testserver").get("/health").headers
    assert "strict-transport-security" not in client.get("/health").headers


def test_docs_hidden():
    for p in ["/docs", "/openapi.json", "/redoc"]:
        assert client.get(p).status_code == 404


# ------------------------------------------------------------------ settings
def _settings_error(env):
    code = "from app.config import Settings; Settings(); print('STARTED')"
    full = {**os.environ, "HANKS_ENV_FILE": "/nonexistent.env", **env}
    full.pop("JWT_SECRET", None) if env.get("JWT_SECRET") is None else None
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "backend", env=full, capture_output=True, text=True)
    return p.stdout + p.stderr


@pytest.mark.parametrize("env", [
    {"JWT_SECRET": ""}, {"JWT_SECRET": "short"},
    {"JWT_SECRET": "change-me-please-use-a-long-random-string"},
    {"JWT_SECRET": "a" * 64}, {"JWT_SECRET": GOOD_SECRET, "CORS_ORIGINS": "*"},
    {"JWT_SECRET": GOOD_SECRET, "CORS_ORIGINS": "https://a.com, *"},
    {"JWT_SECRET": GOOD_SECRET, "JWT_ALGORITHM": "none"},
])
def test_refuses_to_start(env):
    assert "STARTED" not in _settings_error(env)


def test_leaked_secret_refused():
    leaked = None
    envfile = ROOT / "backend" / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            if line.startswith("JWT_SECRET="):
                leaked = line.split("=", 1)[1].strip()
    if leaked:
        assert "STARTED" not in _settings_error({"JWT_SECRET": leaked})


def test_good_settings_start():
    assert "STARTED" in _settings_error({"JWT_SECRET": GOOD_SECRET})


# -------------------------------------------------------------------- tokens
def _tok(payload, key=GOOD_SECRET, alg="HS256"):
    return jwt.encode(payload, key, algorithm=alg)


def _me(token):
    return client.get("/me", headers={"Authorization": "Bearer " + token}).status_code


def _make_user(role="customer", phone="96170123456", pw="Passw0rd123"):
    with SessionLocal() as db:
        u = User(full_name="Test User", phone_number=phone, password_hash=hash_password(pw), role=role)
        db.add(u); db.commit(); return str(u.id)


def test_tokens():
    uid = _make_user()
    now = datetime.now(timezone.utc)
    good = _tok({"sub": uid, "iat": now, "exp": now + timedelta(hours=1)})
    assert _me(good) == 200
    assert _me(_tok({"sub": uid, "iat": now})) == 401                                   # no expiry
    assert _me(_tok({"sub": uid, "iat": now, "exp": now - timedelta(hours=1)})) == 401  # expired
    assert _me(_tok({"sub": uid, "iat": now, "exp": now + timedelta(hours=1)}, key="x" * 40)) == 401  # wrong key
    none_tok = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode() + "." + \
        base64.urlsafe_b64encode(json.dumps({"sub": uid, "exp": int(time.time()) + 3600}).encode()).rstrip(b"=").decode() + "."
    assert _me(none_tok) == 401                                                         # alg=none
    assert _me(_tok({"sub": uid, "iat": now, "exp": now + timedelta(hours=1)}, alg="HS512")) == 401  # other alg
    assert _me("garbage") == 401


# ------------------------------------------------------------------ passwords
def test_password_cap_and_login():
    big = "a1" * 600_000  # ~1.2 MB
    t = time.time()
    r = client.post("/login", json={"phone_number": "96170123456", "password": big})
    assert r.status_code in (413, 422) and time.time() - t < 2
    r = client.post("/signup", json={"full_name": "Bob Test", "phone_number": "96171000001", "password": "a1" * 100})
    assert r.status_code in (413, 422)
    assert client.post("/login", json={"phone_number": "96170123456", "password": "Passw0rd123"}).status_code == 200


def test_login_same_answer_for_unknown_and_wrong():
    a = client.post("/login", json={"phone_number": "96170999999", "password": "Passw0rd123"})
    b = client.post("/login", json={"phone_number": "96170123456", "password": "WrongPass123"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


# -------------------------------------------------------------------- uploads
_ADMIN = {}


def _admin_headers():
    if not _ADMIN:
        _ADMIN["h"] = {"Authorization": "Bearer " + create_access_token(_make_user(role="admin", phone="96170555555"))}
    return _ADMIN["h"]

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
GIF = b"GIF89a" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


def _up(data, name="x.png", ctype="image/png", headers=None):
    return client.post("/admin/uploads/product-image", files={"file": (name, data, ctype)}, headers=headers if headers is not None else _admin_headers())


def test_uploads():
    h = _admin_headers()
    for data, ext in [(PNG, ".png"), (JPG, ".jpg"), (GIF, ".gif"), (WEBP, ".webp")]:
        r = _up(data, headers=h)
        assert r.status_code == 200 and r.json()["image_url"].endswith(ext), r.text
        (UI_DIR / r.json()["image_url"].lstrip("/")).unlink()
    assert _up(b"<html><script>alert(1)</script></html>", "a.png", "image/png", h).status_code == 400   # html pretending to be png
    assert _up(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "a.svg", "image/svg+xml", h).status_code == 400
    assert _up(b"not an image at all", "a.png", "image/png", h).status_code == 400
    assert _up(b"", "a.png", "image/png", h).status_code == 400
    assert _up(PNG + b"\x00" * (5 * 1024 * 1024), "big.png", "image/png", h).status_code == 413
    assert _up(PNG + b"\x00" * (50 * 1024 * 1024), "huge.png", "image/png", h).status_code == 413
    assert _up(PNG, headers={}).status_code == 401                       # not logged in
    cust = {"Authorization": "Bearer " + create_access_token(_make_user(phone="96170444444"))}
    assert _up(PNG, headers=cust).status_code == 403                     # not an admin


# ------------------------------------------------------------------ image urls
@pytest.mark.parametrize("url,ok", [
    ("/img/uploads/abc.png", True), ("https://cdn.example.com/a.jpg", True), (None, True), ("", True),
    ("javascript:alert(1)", False), ("JaVaScRiPt:alert(1)", False), ("//evil.com/a.png", False),
    ("http://example.com/a.png", False), ("data:text/html,<script>1</script>", False),
    ("/img/../backend/.env", False), ("/img/a b.png", False), ("/etc/passwd", False),
    ("/img/a.png\\x", False), ("https://", False),
])
def test_image_url(url, ok):
    from pydantic import ValidationError
    from app.schemas import ProductCreateIn
    try:
        ProductCreateIn(name_en="x", price=1, image_url=url); got = True
    except ValidationError:
        got = False
    assert got == ok


# ------------------------------------------------------------------ rate limit
def test_global_rate_limit_and_login_limit():
    c = TestClient(app, headers={"X-Forwarded-For": "9.9.9.9"})
    codes = [c.post("/login", json={"phone_number": "96170999999", "password": "Passw0rd123"}).status_code for _ in range(14)]
    assert 429 in codes
    c2 = TestClient(app)
    seen = set()
    for _ in range(320):
        seen.add(c2.get("/health").status_code)
    assert 429 in seen


# ----------------------------------------------------------------------- CORS
def test_cors_same_origin_only():
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers
