"""A customer's own orders: list and cancel."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_user
from ..models import Order, User
from ..schemas import CustomerOrderOut
from ..serializers import customer_order_out

router = APIRouter(tags=["orders"])

Lang = Literal["en", "ar"]


@router.get("/orders", response_model=list[CustomerOrderOut])
def my_orders(
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    ).all()
    return [customer_order_out(o, lang) for o in orders]


@router.post("/orders/{order_id}/cancel", response_model=CustomerOrderOut)
def cancel_order(
    order_id: uuid.UUID,
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This order is already being prepared and can no longer be cancelled.",
        )
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return customer_order_out(order, lang)
