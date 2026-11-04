"""Admin-only CRUD for branches (locations + their WhatsApp numbers)."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Branch, User
from ..schemas import AdminBranchOut, BranchCreateIn, BranchUpdateIn
from ..serializers import branch_out

router = APIRouter(prefix="/admin", tags=["admin"])

Lang = Literal["en", "ar"]


@router.get("/branches", response_model=list[AdminBranchOut])
def list_branches(
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    branches = db.scalars(
        select(Branch).order_by(Branch.sort_order, Branch.name_en)
    ).all()
    return [branch_out(b, lang, admin=True) for b in branches]


@router.post("/branches", response_model=AdminBranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(
    body: BranchCreateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    if not body.name_en and not body.name_ar:
        raise HTTPException(status_code=422, detail="Please give the branch a name.")
    if not body.whatsapp_number:
        raise HTTPException(status_code=422, detail="Please enter the branch's WhatsApp number.")
    branch = Branch(**body.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch_out(branch, lang, admin=True)


@router.patch("/branches/{branch_id}", response_model=AdminBranchOut)
def update_branch(
    branch_id: uuid.UUID,
    body: BranchUpdateIn,
    lang: Lang = Query("en"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    db.commit()
    db.refresh(branch)
    return branch_out(branch, lang, admin=True)


@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    branch_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found.")
    db.delete(branch)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
