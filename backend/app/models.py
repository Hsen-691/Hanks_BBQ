"""SQLAlchemy models for Hank's BBQ.

Bilingual fields: every customer-facing name/description has an English and an
Arabic column (name_en / name_ar, description_en / description_ar).
Prices are whole Lebanese Lira stored as BigInteger (no decimals).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120))
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="customer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Deleting a user: the DB cascades the cart away and SET NULLs their past
    # orders (keeping order history). passive_deletes lets Postgres do both.
    cart: Mapped["Cart"] = relationship(
        back_populates="user", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", passive_deletes=True
    )


# Which branches carry a category / an item. Only used when the row's
# all_branches flag is False; if all_branches is True the row is on every branch
# (including branches added later).
category_branches = Table(
    "category_branches",
    Base.metadata,
    Column("category_id", Uuid, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
    Column("branch_id", Uuid, ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True),
)
product_branches = Table(
    "product_branches",
    Base.metadata,
    Column("product_id", Uuid, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("branch_id", Uuid, ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_en: Mapped[str] = mapped_column(String(120), default="")
    name_ar: Mapped[str] = mapped_column(String(120), default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    all_branches: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    branches: Mapped[list["Branch"]] = relationship(secondary=category_branches)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name_en: Mapped[str] = mapped_column(String(160), default="")
    name_ar: Mapped[str] = mapped_column(String(160), default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    description_ar: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    old_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    all_branches: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    branches: Mapped[list["Branch"]] = relationship(secondary=product_branches)

    category: Mapped["Category | None"] = relationship(back_populates="products")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Snapshot of who ordered, so the admin board still shows it if the user is removed.
    customer_name: Mapped[str] = mapped_column(String(120), default="")
    customer_phone: Mapped[str] = mapped_column(String(32), default="")

    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text, default="")  # empty = pickup
    notes: Mapped[str] = mapped_column(Text, default="")
    total_price: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User | None"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshots taken at purchase time, so history never changes when the menu does.
    product_name_en: Mapped[str] = mapped_column(String(160), default="")
    product_name_ar: Mapped[str] = mapped_column(String(160), default="")
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class Branch(Base):
    """A restaurant location. Orders are sent to its WhatsApp number."""
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_en: Mapped[str] = mapped_column(String(120), default="")
    name_ar: Mapped[str] = mapped_column(String(120), default="")
    # Digits only, international format (no +), e.g. 96181600699 -> wa.me/96181600699
    whatsapp_number: Mapped[str] = mapped_column(String(32), default="")
    address_en: Mapped[str] = mapped_column(String(200), default="")
    address_ar: Mapped[str] = mapped_column(String(200), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )