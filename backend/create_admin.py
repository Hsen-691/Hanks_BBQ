"""Create a new admin user, or promote an existing account to admin.

Run from the backend/ folder:
    .venv\\Scripts\\python create_admin.py --name "Owner" --phone 70123456
You'll be prompted for a password if --password is omitted (it is not echoed).
If the phone already has an account, it is promoted to admin (and reactivated);
a password is only set when the account is new.
"""
import argparse
import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Cart, User
from app.security import hash_password, normalize_phone


def _valid_password(p: str) -> bool:
    return len(p) >= 8 and any(c.isalpha() for c in p) and any(c.isdigit() for c in p)


def main() -> None:
    ap = argparse.ArgumentParser(description="Create or promote an admin user.")
    ap.add_argument("--name", help="Full name (new accounts only)")
    ap.add_argument("--phone", help="Phone number")
    ap.add_argument("--password", help="Password (min 8 chars, letters + numbers)")
    args = ap.parse_args()

    phone = normalize_phone(args.phone or input("Phone number: "))
    if len(phone) < 7:
        raise SystemExit("That phone number doesn't look right.")

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.phone_number == phone))
        if user is not None:
            user.role = "admin"
            user.is_active = True
            db.commit()
            print(f"Promoted existing account {phone} to admin.")
            return

        name = (args.name or input("Full name: ")).strip()
        if len(name) < 2:
            raise SystemExit("Please provide a full name.")
        password = args.password or getpass.getpass("Password (min 8, letters + numbers): ")
        if not _valid_password(password):
            raise SystemExit("Password must be at least 8 characters with letters and numbers.")

        user = User(
            full_name=name,
            phone_number=phone,
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(user)
        db.flush()
        db.add(Cart(user_id=user.id))
        db.commit()
        print(f"Created admin account for {phone}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
