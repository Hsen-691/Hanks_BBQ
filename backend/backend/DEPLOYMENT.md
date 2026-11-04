# Deploying Hank's BBQ

The app serves the API **and** the website on one port (default 8000). In
production you put **nginx in front** to handle HTTPS and forward to the app.

> Passwords travel from the browser to the server. **Never run this over plain
> HTTP in production** — always terminate TLS at nginx.

---

## 1. Production secrets file (`hanks.env`)

Keep your secrets **outside the project folder**, so they can never be uploaded or
served with the website. Create this file on the server:

- Linux/macOS: `~/hanks-secrets/hanks.env`
- Windows: `C:\Users\<you>\hanks-secrets\hanks.env`

(The app finds it automatically. To use another path, set the `HANKS_ENV_FILE`
environment variable.) Contents:

```
DATABASE_URL=postgresql+psycopg2://hanks_user:<STRONG-DB-PASSWORD>@localhost:5432/hanks_bbq
JWT_SECRET=<paste the output of the command below>
ACCESS_TOKEN_EXPIRE_MINUTES=10080
APP_PORT=8000
CORS_ORIGINS=
DOCS_ENABLED=false
```

Generate the secret with:  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

- The app **refuses to start** if `JWT_SECRET` is missing, shorter than 32
  characters, a placeholder, or a secret that was leaked before. It also refuses
  `CORS_ORIGINS=*`.
- Changing `JWT_SECRET` logs everyone out (that's fine, and what you want after a leak).
- Leave `CORS_ORIGINS` empty: the app serves the site itself (same origin). Only
  list a real domain if another website must call the API. Never `*`.

## 2. Create the first admin

No admin exists until you make one. On the server:

```
.venv\Scripts\python create_admin.py --name "Owner" --phone 70XXXXXX
```

It prompts for a password (not echoed). Everyone else signs up on the shop; an
admin promotes them from the **Users** tab.

## 3. Run the app as a service

Run it with uvicorn, bound to localhost only (nginx reaches it locally):

```
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips="127.0.0.1"
```

`--proxy-headers` makes the app trust `X-Forwarded-For` from nginx, so the rate
limiter sees each real client IP instead of nginx's.

Keep it running after logout/reboot:
- **Windows:** install it as a service with [NSSM](https://nssm.cc/) pointing at the
  uvicorn command above, or create a Task Scheduler task "At startup".
- **Linux:** a systemd unit running the same uvicorn command.

## 4. nginx in front (TLS + reverse proxy)

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 6m;   # product image uploads (5 MB cap)

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

# Redirect http -> https
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

Get a free certificate with **certbot** (Let's Encrypt) on Linux:
`sudo certbot --nginx -d yourdomain.com`. On Windows, use win-acme.

## 5. Backups

Schedule `backup.bat` daily (see `README.md`). It writes dumps to `C:\\hanks-backups`
(outside the website folder) and reads the DB password from PostgreSQL's
`pgpass.conf`, so no password is stored in the script. Copy the dumps off the
server periodically and test a restore at least once.

**Never** put backups, `.env` files, or the `venv` inside the folder you deploy.

---

## Go-live checklist

- [ ] Strong `JWT_SECRET` and DB password in `hanks.env` (outside the project folder)
- [ ] First admin created with `create_admin.py`; no default/test admin remains
- [ ] App runs as a service, bound to `127.0.0.1`, with `--proxy-headers`
- [ ] nginx terminates HTTPS and proxies to the app; HTTP redirects to HTTPS
- [ ] `CORS_ORIGINS` empty (same-origin), never `*`
- [ ] `python -m pytest backend/tests` passes (run `pip install -r requirements-dev.txt` first)
- [ ] `https://yourdomain.com/backend/.env` and `/.env` return 404
- [ ] Daily backups scheduled and a restore tested
- [ ] Privacy Policy / Terms reviewed by the owner (and a lawyer) for the real
      payment, delivery area, and contact details
