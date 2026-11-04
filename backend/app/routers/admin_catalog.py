"""Admin-only CRUD for categories and menu items."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_admin
from ..models import Branch, Category, Product, User
from ..schemas import (
    AdminCategoryOut,
    AdminProductOut,
    CategoryCreateIn,
    CategoryUpdateIn,
    ProductCreateIn,
    ProductUpdateIn,
)
from ..serializers import admin_category_out, admin_product_out

router = APIRouter(prefix="/admin", tags=["admin"])

Lang = Literal["en", "ar"]


def _set_branches(
    db: Session,
    obj: Category | Product,
    all_branches: bool | None,
    branch_ids: list[uuid.UUID] | None,
) -> None:
    """Apply the "which branches carry this" choice to a category or item.

    all_branches=True means every branch (current and future). Otherwise at
    least one branch must be picked.
    """
    if all_branches is None and branch_ids is None:
        return  # not part of this request: leave as is
    new_all = obj.all_branches if all_branches is None else all_branches
    if new_all:
        obj.all_branches = True
        obj.branches = []
        return
    ids = set(branch_ids) if branch_ids is not None else {b.id for b in obj.branches}
    if not ids:
        raise HTTPException(
            status_code=422, detail="Please pick at least one branch (or choose all branches)."
        )
    found = db.scalars(select(Branch).where(Branch.id.in_(ids))).all()
    if len(found) != len(ids):
        raise HTTPException(status_code=422, detail="One of the chosen branches does not exist.")
    obj.all_branches = False
    obj.branches = list(found)


# ---------- categories ----------


@router.get("/categories", response_model=list[AdminCategoryOut])
def list_categories(
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    cats = db.scalars(
        select(Category)
        .options(selectinload(Category.branches))
        .order_by(Category.sort_order, Category.name_en)
    ).all()
    return [admin_category_out(c, lang) for c in cats]


@router.post("/categories", response_model=AdminCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    if not body.name_en and not body.name_ar:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please give the category a name in at least one language.",
        )
    cat = Category(
        name_en=body.name_en,
        name_ar=body.name_ar,
        sort_order=body.sort_order,
        image_url=body.image_url,
    )
    _set_branches(db, cat, body.all_branches, body.branch_ids)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return admin_category_out(cat, lang)


@router.patch("/categories/{category_id}", response_model=AdminCategoryOut)
def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    data = body.model_dump(exclude_unset=True)
    _set_branches(db, cat, data.pop("all_branches", None), data.pop("branch_ids", None))
    for field, value in data.items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return admin_category_out(cat, lang)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    # Products keep existing; their category_id is set to NULL by the FK rule.
    db.delete(cat)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- products ----------


@router.get("/products", response_model=list[AdminProductOut])
def list_products(
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    # Admin sees every item, available or not.
    prods = db.scalars(
        select(Product)
        .options(selectinload(Product.branches), selectinload(Product.category))
        .order_by(Product.sort_order, Product.name_en)
    ).all()
    return [admin_product_out(p, lang) for p in prods]


def _check_category(db: Session, category_id: uuid.UUID | None) -> None:
    if category_id is not None and db.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="That category does not exist.")


@router.post("/products", response_model=AdminProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    if not body.name_en and not body.name_ar:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please give the item a name in at least one language.",
        )
    _check_category(db, body.category_id)
    product = Product(**body.model_dump(exclude={"all_branches", "branch_ids"}))
    _set_branches(db, product, body.all_branches, body.branch_ids)
    db.add(product)
    db.commit()
    db.refresh(product)
    return admin_product_out(product, lang)


@router.patch("/products/{product_id}", response_model=AdminProductOut)
def update_product(
    product_id: uuid.UUID,
    body: ProductUpdateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    data = body.model_dump(exclude_unset=True)
    if "category_id" in data:
        _check_category(db, data["category_id"])
    _set_branches(db, product, data.pop("all_branches", None), data.pop("branch_ids", None))
    for field, value in data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return admin_product_out(product, lang)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    # Order history keeps its snapshot; order_items.product_id becomes NULL.
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)