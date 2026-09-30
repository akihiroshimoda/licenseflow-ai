from enum import Enum

from pydantic import BaseModel, Field

from licenseflow_ai.models.approval import Approval
from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.product import Product


class DealStatus(str, Enum):
    NEW = "new"
    NEEDS_INFORMATION = "needs_information"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Deal(BaseModel):
    customer: Customer
    product: Product

    contract_term_years: int = Field(gt=0)
    discount_percent: float = Field(ge=0, le=100)

    status: DealStatus = DealStatus.NEW

    legal_review_required: bool = False
    approval_required: bool = False

    approvals: list[Approval] = Field(default_factory=list)

