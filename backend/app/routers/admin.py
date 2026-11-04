"""Admin-only: the live orders board and order status changes.

(Admin CRUD for products/categories/users and image upload come next.)
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_admin
from ..models import Order, User
from ..schemas import AdminOrderOut, UpdateStatusIn
from ..serializers import admin_order_out

router = APIRouter(prefix="/admin", tags=["admin"])

Lang = Literal["en", "ar"]


@router.get("/orders", response_model=list[AdminOrderOut])
def list_orders(
    limit: int = Query(200, ge=1, le=500),
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(limit)
    ).all()
    return [admin_order_out(o, lang) for o in orders]


@router.patch("/orders/{order_id}/status", response_model=AdminOrderOut)
def update_order_status(
    order_id: uuid.UUID,
    body: UpdateStatusIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )
    order.status = body.status
    db.commit()
    db.refresh(order)
    return admin_order_out(order, lang)
