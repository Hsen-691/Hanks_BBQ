"""Sign up, log in, and 'who am I'."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Cart, User
from ..ratelimit import limiter
from ..schemas import LoginIn, MeOut, SignupIn, TokenOut
from ..security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=TokenOut)
@limiter.limit("5/minute")
def signup(request: Request, body: SignupIn, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.scalar(select(User).where(User.phone_number == body.phone_number))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this phone number already exists. Please sign in.",
        )

    user = User(
        full_name=body.full_name,
        phone_number=body.phone_number,
        password_hash=hash_password(body.password),
        role="customer",
    )
    db.add(user)
    db.flush()  # assigns user.id
    db.add(Cart(user_id=user.id))
    db.commit()

    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
def login(request: Request, body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.phone_number == body.phone_number))
    # Same message AND same timing whether the phone or the password is wrong, so
    # we don't reveal which phone numbers have accounts: when there is no such
    # user we still do one full password check against a dummy hash.
    password_ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number or password is incorrect.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact the restaurant.",
        )
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
