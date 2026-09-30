import httpx

from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.product import Product


CRM_BASE_URL = "http://127.0.0.1:8000"


def get_customer_by_name(name: str) -> Customer:
    response = httpx.get(
        f"{CRM_BASE_URL}/crm/customers",
        params={"name": name},
        timeout=5.0,
    )

    if response.status_code == 404:
        raise ValueError(
            f"Customer not found in CRM: {name}"
        )

    response.raise_for_status()

    return Customer.model_validate(
        response.json()
    )


def get_product_by_name(name: str) -> Product:
    response = httpx.get(
        f"{CRM_BASE_URL}/crm/products",
        params={"name": name},
        timeout=5.0,
    )

    if response.status_code == 404:
        raise ValueError(
            f"Product not found in CRM: {name}"
        )

    response.raise_for_status()

    return Product.model_validate(
        response.json()
    )