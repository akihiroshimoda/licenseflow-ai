from pydantic import BaseModel, Field


class DealRequest(BaseModel):
    customer_name: str | None = None
    product_name: str | None = None
    use_case: str | None = None
    region: str | None = None

    contract_term_years: int | None = Field(
        default=None,
        gt=0,
    )

    discount_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    commercial_rationale: str | None = None