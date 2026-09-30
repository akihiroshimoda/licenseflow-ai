from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from licenseflow_ai.database.base import Base

class CustomerDB(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String)
    account_tier: Mapped[str] = mapped_column(String)


class ProductDB(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    base_price: Mapped[float] = mapped_column(Float)


class DealDB(Base):
    __tablename__ = 'deals'
    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))

    contract_term_years: Mapped[int] = mapped_column(Integer)
    discount_percent: Mapped[float] = mapped_column(Float)

    status: Mapped[str] = mapped_column(String, default='new')
    legal_preview_required: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped['CustomerDB'] = relationship()
    product: Mapped['ProductDB'] = relationship()

