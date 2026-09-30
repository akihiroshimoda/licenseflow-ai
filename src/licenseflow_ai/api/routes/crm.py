from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session 

from licenseflow_ai.api.dependencies import get_db
from licenseflow_ai.database.models import CustomerDB, DealDB, ProductDB
from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.deal import Deal
from licenseflow_ai.models.product import Product


router = APIRouter(prefix='/crm', tags=['CRM'])

@router.get("/customers", response_model=Customer)
def find_customer_by_name(
    name: str,
    db: Session = Depends(get_db),
) -> Customer:
    customer = db.scalar(
        select(CustomerDB).where(
            func.lower(CustomerDB.name) == name.lower()
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return Customer(
        customer_id=customer.customer_id,
        name=customer.name,
        region=customer.region,
        account_tier=customer.account_tier,
    )


@router.get("/products", response_model=Product)
def find_product_by_name(
    name: str,
    db: Session = Depends(get_db),
) -> Product:
    product = db.scalar(
        select(ProductDB).where(
            func.lower(ProductDB.name) == name.lower()
        )
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return Product(
        product_id=product.product_id,
        name=product.name,
        category=product.category,
        base_price=product.base_price,
    )

@router.get('/deals/{deal_id}', response_model=Deal)
def get_deal(
    deal_id: str,
    db: Session = Depends(get_db),
) -> Deal:
    deal = db.scalar(
        select(DealDB).where(DealDB.deal_id==deal_id)
    )

    if deal is None:
        raise HTTPException(status_code=404, detail='Deal not found')

    customer = Customer(
        customer_id=deal.customer.customer_id,
        name=deal.customer.name,
        region=deal.customer.region,
        account_tier=deal.customer.account_tier,
    )

    product = Product(
        product_id=deal.product.product_id,
        name=deal.product.name,
        category=deal.product.category,
        base_price=deal.product.base_price,
    )

    return Deal(
        customer = customer,
        product = product,
        contract_term_years = deal.contract_term_years,
        discount_percent = deal.discount_percent,
        status = deal.status,
        legal_preview_required = deal.legal_preview_required,
        approval_required = deal.approval_required,
    )