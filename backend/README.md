# Hank's BBQ — backend

FastAPI + PostgreSQL. Serves the JSON API **and** the website (the `../` UI folder)
on one port, so `js/api.js` talks to the same origin.

## Stack
- FastAPI, Uvicorn
- PostgreSQL 17, SQLAlchemy 2.0, Alembic migrations
- Auth: JWT (PyJWT) + argon2 password hashing (passlib)
- Prices: whole **Lebanese Lira** (BigInteger, no decimals)
- Menu text is **bilingual** — every name/description has `_en` and `_ar`

## One-time setup
1. PostgreSQL 17 must be running (service `postgresql-x64-17`, superuser `postgres`/`postgres`).
2. Create the database + app role (already done on this machine):
   ```
   CREATE ROLE hanks_user LOGIN PASSWORD 'hanks_password';
   CREATE DATABASE hanks_bbq OWNER hanks_user;
   ```
3. Python **3.11** venv (3.14 breaks psycopg2):
   ```
   py -3.11 -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill it in (a working `.env` is already present here).
5. Apply migrations:
   ```
   .venv\Scripts\alembic upgrade head
   ```

## Run
```
start.bat
```
or:
```
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
```
Then open http://localhost:8000 (shop) and http://localhost:8000/admin.html (admin).

## Seed the menu
Load the real Hank's BBQ menu (11 categories, 149 items, bilingual, LL prices):
```
.venv\Scripts\python seed.py
```
Idempotent — it clears and reloads categories/products; customer accounts and
order history are left alone. Edit the `CATEGORIES` / `PRODUCTS` lists in
`seed.py` to change what gets loaded.

## Database changes
After editing `app/models.py`:
```
.venv\Scripts\alembic revision --autogenerate -m "what changed"
.venv\Scripts\alembic upgrade head
```

## Endpoints so far
- Auth: `POST /signup`, `POST /login` -> `{ access_token }`; `GET /me`
- Catalog: `GET /categories?lang=en|ar`, `GET /products?lang=en|ar`
- Cart: `GET /cart`, `POST /cart/items`, `DELETE /cart/items/{product_id}?quantity=1`,
  `DELETE /cart`, `POST /cart/checkout` (`{ delivery_address, notes }`)
- Customer orders: `GET /orders`, `POST /orders/{id}/cancel`
- Admin orders: `GET /admin/orders?limit=200`, `PATCH /admin/orders/{id}/status`
- Admin categories: `GET/POST /admin/categories`, `PATCH/DELETE /admin/categories/{id}`
- Admin products: `GET/POST /admin/products`, `PATCH/DELETE /admin/products/{id}`
- Admin users: `GET /admin/users`, `PATCH /admin/users/{id}/{promote|demote|activate|deactivate}`, `DELETE /admin/users/{id}`
- Admin upload: `POST /admin/uploads/product-image` (multipart `file`) -> `{ image_url }`
- Branches: `GET /branches` (public), `GET/POST /admin/branches`, `PATCH/DELETE /admin/branches/{id}`
- `GET /health`

**Ordering is via WhatsApp:** the shop sends each order to the selected branch's
WhatsApp number (`wa.me/<number>?text=<order>`) instead of saving it. The branch
selector sits under the header; branches are managed in the admin's Branches tab.
The `/cart/checkout` and order endpoints still exist but the shop no longer uses
them, so the admin Orders board stays empty.

Notes:
- Order totals are recomputed on the server from stored prices; order items
  snapshot the product name (both languages) and unit price at purchase time, so
  deleting a product/user/category never damages past orders.
- Admin create/update take bilingual fields (`name_en`/`name_ar`,
  `description_en`/`description_ar`); an "offer" is just `price` + a higher
  `old_price`; hide an item with `is_available=false`.
- An admin cannot demote/deactivate/delete their own account (lockout guard).

## Rate limiting
Login and signup are rate limited per client IP (slowapi): `/login` 10/min,
`/signup` 5/min. Exceeding it returns 429 `{ detail: ... }`, which the shop shows
as "Too many requests…". Behind nginx, pass the real client IP and key the limiter
on `X-Forwarded-For` (see `app/ratelimit.py`), or every request looks like the proxy.

## Backups
`backup.bat` writes a compressed dump to `backend/backups/` and prunes dumps older
than 14 days. Run it manually, or schedule it daily (run once as Administrator):
```
schtasks /Create /SC DAILY /ST 03:00 /TN "HanksBBQ Backup" /TR "\"%CD%\backup.bat\""
```
Restore a dump into a fresh/clean database:
```
.venv\Scripts\python -c "import os;os.environ['PGPASSWORD']='hanks_password'"
"C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -U hanks_user -h localhost -d hanks_bbq --clean "backups\<file>.dump"
```
(`backups/` is git-ignored.)

## First admin account
No admin exists until you create one:
```
.venv\Scripts\python create_admin.py --name "Owner" --phone 70XXXXXX
```
It prompts for a password (not echoed), or pass `--password`. If the phone already
has an account it's promoted to admin. After the first admin, promote staff from
the admin panel's **Users** tab.

## Going live
See `DEPLOYMENT.md` for nginx + HTTPS, running as a service, and the go-live
checklist (strong secrets, no default admin, backups, proxy headers).
