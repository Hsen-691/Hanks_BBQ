"""Pydantic request/response models for auth, catalog, cart, and orders."""
import datetime
import uuid

from pydantic import BaseModel, Field, field_validator

from .constants import ORDER_STATUSES
from .security import MAX_PASSWORD_LENGTH, normalize_phone


def _safe_image_url(v: str | None) -> str | None:
    """Only allow our own uploaded/static images ("/img/...") or https links.
    Rejects javascript:, data:, //host (protocol-relative), plain http://, and
    anything with spaces, backslashes or "..".
    """
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    if len(v) > 500 or any(c.isspace() or ord(c) < 32 or c == "\\" for c in v) or ".." in v:
        raise ValueError("That image link is not allowed.")
    if v.startswith("/img/") and not v.startswith("//"):
        return v
    if v.lower().startswith("https://") and len(v) > len("https://") + 3:
        return v
    raise ValueError("That image link is not allowed.")

# ---------- auth ----------


class SignupIn(BaseModel):
    full_name: str = Field(max_length=120)
    phone_number: str = Field(max_length=64)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)

    @field_validator("full_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Please enter your full name.")
        return v

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = normalize_phone(v)
        if not _valid_phone(v):
            raise ValueError("Please enter a valid phone number.")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (len(v) >= 8 and any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Use at least 8 characters, with letters and numbers.")
        return v


class LoginIn(BaseModel):
    phone_number: str = Field(max_length=64)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    role: str

    model_config = {"from_attributes": True}


def _valid_phone(v: str) -> bool:
    # v has already been reduced to digits by normalize_phone.
    return v.isdigit() and 7 <= len(v) <= 15


# ---------- catalog ----------


class CategoryOut(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = []
    id: uuid.UUID
    name: str  # resolved to the requested language (?lang=en|ar)
    name_en: str
    name_ar: str
    image_url: str | None = None
    sort_order: int


class ProductOut(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = []
    id: uuid.UUID
    category_id: uuid.UUID | None = None
    name: str  # resolved to the requested language
    name_en: str
    name_ar: str
    description: str  # resolved to the requested language
    description_en: str
    description_ar: str
    price: int
    old_price: int | None = None
    image_url: str | None = None
    is_available: bool


# ---------- cart ----------


class AddToCartIn(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemOut(BaseModel):
    product_id: uuid.UUID
    product_name: str
    product_name_en: str
    product_name_ar: str
    image_url: str | None = None
    unit_price: int
    quantity: int
    sub_total: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: int
    item_count: int


# ---------- checkout & orders ----------


class CheckoutIn(BaseModel):
    delivery_address: str = Field(default="", max_length=500)  # empty = pickup
    notes: str = Field(default="", max_length=500)


class CustomerOrderItemOut(BaseModel):
    product_name: str
    product_name_en: str
    product_name_ar: str
    quantity: int
    price_at_purchase: int


class CustomerOrderOut(BaseModel):
    order_id: uuid.UUID
    status: str
    created_at: datetime.datetime
    items: list[CustomerOrderItemOut]
    delivery_address: str
    notes: str
    total: int


class AdminOrderItemOut(BaseModel):
    product_name: str
    product_name_en: str
    product_name_ar: str
    quantity: int


class AdminOrderOut(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime.datetime
    items: list[AdminOrderItemOut]
    delivery_address: str
    notes: str
    total_price: int
    full_name: str
    phone_number: str


class UpdateStatusIn(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        if v not in ORDER_STATUSES:
            raise ValueError("Unknown order status.")
        return v


# ---------- admin: categories ----------


class CategoryCreateIn(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    name_en: str = Field(default="", max_length=120)
    name_ar: str = Field(default="", max_length=120)
    sort_order: int = 0
    image_url: str | None = None

    @field_validator("name_en", "name_ar")
    @classmethod
    def _trim(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("image_url")
    @classmethod
    def _image_url(cls, v: str | None) -> str | None:
        return _safe_image_url(v)



class CategoryUpdateIn(BaseModel):
    all_branches: bool | None = None
    branch_ids: list[uuid.UUID] | None = Field(default=None, max_length=100)
    name_en: str | None = Field(default=None, max_length=120)
    name_ar: str | None = Field(default=None, max_length=120)
    sort_order: int | None = None
    image_url: str | None = None

    @field_validator("image_url")
    @classmethod
    def _image_url(cls, v: str | None) -> str | None:
        return _safe_image_url(v)



class AdminCategoryOut(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = []
    id: uuid.UUID
    name: str
    name_en: str
    name_ar: str
    image_url: str | None = None
    sort_order: int


# ---------- admin: products ----------


class ProductCreateIn(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    name_en: str = Field(default="", max_length=160)
    name_ar: str = Field(default="", max_length=160)
    description_en: str = ""
    description_ar: str = ""
    price: int = Field(ge=0)
    old_price: int | None = Field(default=None, ge=0)
    is_available: bool = True
    category_id: uuid.UUID | None = None
    sort_order: int = 0
    image_url: str | None = None

    @field_validator("name_en", "name_ar", "description_en", "description_ar")
    @classmethod
    def _trim(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("image_url")
    @classmethod
    def _image_url(cls, v: str | None) -> str | None:
        return _safe_image_url(v)



class ProductUpdateIn(BaseModel):
    all_branches: bool | None = None
    branch_ids: list[uuid.UUID] | None = Field(default=None, max_length=100)
    name_en: str | None = Field(default=None, max_length=160)
    name_ar: str | None = Field(default=None, max_length=160)
    description_en: str | None = None
    description_ar: str | None = None
    price: int | None = Field(default=None, ge=0)
    old_price: int | None = Field(default=None, ge=0)
    is_available: bool | None = None
    category_id: uuid.UUID | None = None
    sort_order: int | None = None
    image_url: str | None = None

    @field_validator("image_url")
    @classmethod
    def _image_url(cls, v: str | None) -> str | None:
        return _safe_image_url(v)



class AdminProductOut(BaseModel):
    all_branches: bool = True
    branch_ids: list[uuid.UUID] = []
    id: uuid.UUID
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    name: str
    name_en: str
    name_ar: str
    description: str
    description_en: str
    description_ar: str
    price: int
    old_price: int | None = None
    image_url: str | None = None
    is_available: bool
    sort_order: int


# ---------- admin: users & uploads ----------


class AdminUserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UploadOut(BaseModel):
    image_url: str


# ---------- branches ----------


def _digits(v: str) -> str:
    import re
    return re.sub(r"\D", "", v or "")


class BranchOut(BaseModel):
    id: uuid.UUID
    name: str
    name_en: str
    name_ar: str
    whatsapp_number: str
    address: str
    address_en: str
    address_ar: str
    sort_order: int


class AdminBranchOut(BranchOut):
    is_active: bool


class BranchCreateIn(BaseModel):
    name_en: str = Field(default="", max_length=120)
    name_ar: str = Field(default="", max_length=120)
    whatsapp_number: str = Field(default="", max_length=32)
    address_en: str = Field(default="", max_length=200)
    address_ar: str = Field(default="", max_length=200)
    sort_order: int = 0
    is_active: bool = True

    @field_validator("name_en", "name_ar", "address_en", "address_ar")
    @classmethod
    def _trim(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("whatsapp_number")
    @classmethod
    def _wa(cls, v: str) -> str:
        return _digits(v)


class BranchUpdateIn(BaseModel):
    name_en: str | None = Field(default=None, max_length=120)
    name_ar: str | None = Field(default=None, max_length=120)
    whatsapp_number: str | None = Field(default=None, max_length=32)
    address_en: str | None = Field(default=None, max_length=200)
    address_ar: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("whatsapp_number")
    @classmethod
    def _wa(cls, v: str | None) -> str | None:
        return _digits(v) if v is not None else None