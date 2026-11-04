"""Password hashing (argon2), JWT access tokens, and phone normalization."""
import re
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import settings

# argon2 is the password hashing promised on the site's privacy page.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Longest password we will ever hash or verify. Without a cap, a 1 MB "password"
# would tie up the (deliberately slow) argon2 hasher.
MAX_PASSWORD_LENGTH = 128


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if len(plain) > MAX_PASSWORD_LENGTH:
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


# A real argon2 hash of a throwaway string. Login verifies against this when the
# phone number has no account, so "unknown phone" and "wrong password" take the
# same time and cannot be told apart by timing.
DUMMY_HASH = pwd_context.hash("not-a-real-password-just-for-timing")


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError on any invalid/expired token.

    Only our one configured algorithm is accepted (so alg=none is rejected) and a
    token with no expiry is rejected.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub"]},
    )


def normalize_phone(raw: str) -> str:
    """Reduce a typed phone number to digits only, so the same person maps to
    one account no matter how they type it.

    We drop a leading '+' and every separator, so '+961 70 123 456' and
    '96170123456' become the same stored value. (Note: this does NOT reconcile a
    local number like '70123456' with its international form '+96170123456' --
    that needs a default country code; see the project notes.)
    """
    return re.sub(r"\D", "", (raw or "")[:64])
