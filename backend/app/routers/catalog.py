"""Public menu: categories and available products."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Branch, Category, Product
from ..schemas import BranchOut, CategoryOut, ProductOut
from ..serializers import branch_out, category_out, product_out

router = APIRouter(tags=["catalog"])

Lang = Literal["en", "ar"]


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    lang: Lang = Query("en"), db: Session = Depends(get_db)
) -> list[dict]:
    cats = db.scalars(
        select(Category)
        .options(selectinload(Category.branches))
        .order_by(Category.sort_order, Category.name_en)
    ).all()
    return [category_out(c, lang) for c in cats]


@router.get("/products", response_model=list[ProductOut])
def list_products(
    lang: Lang = Query("en"), db: Session = Depends(get_db)
) -> list[dict]:
    # Public menu shows only items the owner has marked available.
    prods = db.scalars(
        select(Product)
        .options(selectinload(Product.branches))
        .where(Product.is_available.is_(True))
        .order_by(Product.sort_order, Product.name_en)
    ).all()
    return [product_out(p, lang) for p in prods]


@router.get("/branches", response_model=list[BranchOut])
def list_branches(
    lang: Lang = Query("en"), db: Session = Depends(get_db)
) -> list[dict]:
    branches = db.scalars(
        select(Branch)
        .where(Branch.is_active.is_(True))
        .order_by(Branch.sort_order, Branch.name_en)
    ).all()
    return [branch_out(b, lang) for b in branches]