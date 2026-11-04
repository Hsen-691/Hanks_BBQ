"""Admin-only: list users and change their role / active state."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import User
from ..schemas import AdminUserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[User]:
    return list(
        db.scalars(select(User).order_by(User.created_at.desc())).all()
    )


def _load_other_user(db: Session, admin: User, user_id: uuid.UUID) -> User:
    if user_id == admin.id:
        # Guard against an admin locking themselves out or deleting themselves.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own account here.",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.patch("/users/{user_id}/promote", response_model=AdminUserOut)
def promote(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = _load_other_user(db, admin, user_id)
    user.role = "admin"
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/demote", response_model=AdminUserOut)
def demote(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = _load_other_user(db, admin, user_id)
    user.role = "customer"
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/activate", response_model=AdminUserOut)
def activate(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = _load_other_user(db, admin, user_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=AdminUserOut)
def deactivate(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = _load_other_user(db, admin, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    user = _load_other_user(db, admin, user_id)
    # Their past orders keep the name/phone snapshot (orders.user_id -> NULL).
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
