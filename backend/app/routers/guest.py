"""Guest checkout: place an order without an account.

The order still lands on the admin board (user_id is NULL, with the name/phone
the guest typed). Totals are computed here from our own prices. Rate limited.
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, Product
from ..ratelimit import limiter
from ..schemas import CustomerOrderOut
from ..security import normalize_phone
from ..serializers import customer_order_out

router = APIRouter(tags=["guest"])

Lang = Literal["en", "ar"]


class GuestItemIn(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=99)


class GuestCheckoutIn(BaseModel):
    customer_name: str = Field(default="", max_length=120)
    customer_phone: str = Field(default="", max_length=32)
    delivery_address: str = Field(default="", max_length=500)  # empty = pickup
    notes: str = Field(default="", max_length=500)
    items: list[GuestItemIn] = Field(min_length=1, max_length=100)


@router.post("/guest/checkout", response_model=CustomerOrderOut)
@limiter.limit("20/minute")
def guest_checkout(
    request: Request,
    body: GuestCheckoutIn,
    lang: Lang = Query("en"),
    db: Session = Depends(get_db),
) -> dict:
    # Merge duplicate product ids and cap each line.
    merged: dict[uuid.UUID, int] = {}
    for it in body.items:
        merged[it.product_id] = min(merged.get(it.product_id, 0) + it.quantity, 99)

    order = Order(
        user_id=None,
        customer_name=(body.customer_name or "").strip(),
        customer_phone=normalize_phone(body.customer_phone),
        status="pending",
        delivery_address=body.delivery_address.strip(),
        notes=body.notes.strip(),
    )
    db.add(order)
    db.flush()

    total = 0
    for pid, qty in merged.items():
        p = db.get(Product, pid)
        if p is None or not p.is_available:
            continue
        total += p.price * qty
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name_en=p.name_en,
                product_name_ar=p.name_ar,
                unit_price=p.price,
                quantity=qty,
            )
        )

    if total == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="None of those items are available right now.",
        )

    order.total_price = total
    db.commit()
    db.refresh(order)
    return customer_order_out(order, lang)
