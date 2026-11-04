"""Turn models into the dict shapes the frontend expects.

The shop stores two languages per item. `lang` ("en" or "ar") picks which one
fills the resolved `name` / `description` fields; both raw languages are always
included too, so the frontend can switch instantly without another request.
"""
from .models import Branch, Cart, CartItem, Category, Order, OrderItem, Product


def _pick(en: str, ar: str, lang: str) -> str:
    primary, fallback = (ar, en) if lang == "ar" else (en, ar)
    return primary or fallback or ""


def category_out(c: Category, lang: str = "en") -> dict:
    return {
        "id": c.id,
        "name": _pick(c.name_en, c.name_ar, lang),
        "name_en": c.name_en,
        "name_ar": c.name_ar,
        "image_url": c.image_url,
        "sort_order": c.sort_order,
        "all_branches": c.all_branches,
        "branch_ids": [b.id for b in c.branches],
    }


def product_out(p: Product, lang: str = "en") -> dict:
    return {
        "id": p.id,
        "category_id": p.category_id,
        "name": _pick(p.name_en, p.name_ar, lang),
        "name_en": p.name_en,
        "name_ar": p.name_ar,
        "description": _pick(p.description_en, p.description_ar, lang),
        "description_en": p.description_en,
        "description_ar": p.description_ar,
        "price": p.price,
        "old_price": p.old_price,
        "image_url": p.image_url,
        "is_available": p.is_available,
        "all_branches": p.all_branches,
        "branch_ids": [b.id for b in p.branches],
    }


# ---------- cart ----------


def cart_item_out(ci: CartItem, lang: str = "en") -> dict:
    p = ci.product
    unit = p.price
    return {
        "product_id": ci.product_id,
        "product_name": _pick(p.name_en, p.name_ar, lang),
        "product_name_en": p.name_en,
        "product_name_ar": p.name_ar,
        "image_url": p.image_url,
        "unit_price": unit,
        "quantity": ci.quantity,
        "sub_total": unit * ci.quantity,
    }


def cart_out(cart: Cart, lang: str = "en") -> dict:
    items = sorted(
        (cart_item_out(ci, lang) for ci in cart.items),
        key=lambda i: i["product_name"].lower(),
    )
    return {
        "items": items,
        "total": sum(i["sub_total"] for i in items),
        "item_count": sum(i["quantity"] for i in items),
    }


# ---------- orders ----------


def _order_item_name(oi: OrderItem, lang: str) -> dict:
    return {
        "product_name": _pick(oi.product_name_en, oi.product_name_ar, lang),
        "product_name_en": oi.product_name_en,
        "product_name_ar": oi.product_name_ar,
    }


def customer_order_out(o: Order, lang: str = "en") -> dict:
    return {
        "order_id": o.id,
        "status": o.status,
        "created_at": o.created_at,
        "items": [
            {**_order_item_name(oi, lang), "quantity": oi.quantity, "price_at_purchase": oi.unit_price}
            for oi in o.items
        ],
        "delivery_address": o.delivery_address,
        "notes": o.notes,
        "total": o.total_price,
    }


def admin_order_out(o: Order, lang: str = "en") -> dict:
    return {
        "id": o.id,
        "status": o.status,
        "created_at": o.created_at,
        "items": [
            {**_order_item_name(oi, lang), "quantity": oi.quantity} for oi in o.items
        ],
        "delivery_address": o.delivery_address,
        "notes": o.notes,
        "total_price": o.total_price,
        "full_name": o.customer_name,
        "phone_number": o.customer_phone,
    }


# ---------- admin ----------


def admin_category_out(c: Category, lang: str = "en") -> dict:
    return {
        "id": c.id,
        "name": _pick(c.name_en, c.name_ar, lang),
        "name_en": c.name_en,
        "name_ar": c.name_ar,
        "image_url": c.image_url,
        "sort_order": c.sort_order,
        "all_branches": c.all_branches,
        "branch_ids": [b.id for b in c.branches],
    }


def branch_out(b: Branch, lang: str = "en", admin: bool = False) -> dict:
    data = {
        "id": b.id,
        "name": _pick(b.name_en, b.name_ar, lang),
        "name_en": b.name_en,
        "name_ar": b.name_ar,
        "whatsapp_number": b.whatsapp_number,
        "address": _pick(b.address_en, b.address_ar, lang),
        "address_en": b.address_en,
        "address_ar": b.address_ar,
        "sort_order": b.sort_order,
    }
    if admin:
        data["is_active"] = b.is_active
    return data


def admin_product_out(p: Product, lang: str = "en") -> dict:
    cat = p.category
    return {
        "id": p.id,
        "category_id": p.category_id,
        "category_name": _pick(cat.name_en, cat.name_ar, lang) if cat else None,
        "name": _pick(p.name_en, p.name_ar, lang),
        "name_en": p.name_en,
        "name_ar": p.name_ar,
        "description": _pick(p.description_en, p.description_ar, lang),
        "description_en": p.description_en,
        "description_ar": p.description_ar,
        "price": p.price,
        "old_price": p.old_price,
        "image_url": p.image_url,
        "is_available": p.is_available,
        "sort_order": p.sort_order,
        "all_branches": p.all_branches,
        "branch_ids": [b.id for b in p.branches],
    }