"""The signed-in customer's cart, and turning it into an order at checkout."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Cart, CartItem, Order, OrderItem, Product, User
from ..schemas import AddToCartIn, CartOut, CheckoutIn, CustomerOrderOut
from ..serializers import cart_out, customer_order_out

router = APIRouter(tags=["cart"])

Lang = Literal["en", "ar"]


def _get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


@router.get("/cart", response_model=CartOut)
def get_cart(
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    cart = _get_or_create_cart(db, user)
    db.commit()
    return cart_out(cart, lang)


@router.post("/cart/items", response_model=CartOut)
def add_item(
    body: AddToCartIn,
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    cart = _get_or_create_cart(db, user)
    product = db.get(Product, body.product_id)
    if product is None or not product.is_available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sorry, that item is not available right now.",
        )
    item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.product_id == body.product_id
        )
    )
    if item is not None:
        item.quantity = min(item.quantity + body.quantity, 99)
    else:
        db.add(CartItem(cart_id=cart.id, product_id=body.product_id, quantity=body.quantity))
    db.commit()
    db.refresh(cart)
    return cart_out(cart, lang)


@router.delete("/cart/items/{product_id}", response_model=CartOut)
def remove_item(
    product_id: uuid.UUID,
    quantity: int = Query(1, ge=1),
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    cart = _get_or_create_cart(db, user)
    item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.product_id == product_id
        )
    )
    if item is not None:
        item.quantity -= quantity
        if item.quantity <= 0:
            db.delete(item)
        db.commit()
        db.refresh(cart)
    return cart_out(cart, lang)


@router.delete("/cart", response_model=CartOut)
def clear_cart(
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    cart = _get_or_create_cart(db, user)
    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart_out(cart, lang)


@router.post("/cart/checkout", response_model=CustomerOrderOut)
def checkout(
    body: CheckoutIn,
    lang: Lang = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    cart = _get_or_create_cart(db, user)
    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty."
        )

    unavailable = [
        ci.product.name_en or ci.product.name_ar
        for ci in cart.items
        if ci.product is None or not ci.product.is_available
    ]
    if unavailable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some items are no longer available: "
            + ", ".join(unavailable)
            + ". Please remove them and try again.",
        )

    order = Order(
        user_id=user.id,
        customer_name=user.full_name,
        customer_phone=user.phone_number,
        status="pending",
        delivery_address=body.delivery_address.strip(),  # empty = pickup
        notes=body.notes.strip(),
    )
    db.add(order)
    db.flush()

    # Totals are computed here from our own prices -- never trust a browser total.
    total = 0
    for ci in cart.items:
        p = ci.product
        unit = p.price
        total += unit * ci.quantity
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name_en=p.name_en,
                product_name_ar=p.name_ar,
                unit_price=unit,
                quantity=ci.quantity,
            )
        )
    order.total_price = total

    for ci in list(cart.items):  # empty the cart
        db.delete(ci)

    db.commit()
    db.refresh(order)
    return customer_order_out(order, lang)
