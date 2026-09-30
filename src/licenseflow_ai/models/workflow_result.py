from enum import Enum

from pydantic import BaseModel, Field

from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.deal_request import DealRequest
from licenseflow_ai.models.product import Product

class WorkflowStatus(str, Enum):
    NEEDS_INFORMATION = "needs_information"
    AWAITING_APPROVAL = "awaiting_approval"
    READY_FOR_PROCESSING = "ready_for_processing"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkflowResult(BaseModel):
    request: DealRequest

    customer: Customer | None = None
    product: Product | None = None

    missing_information: list[str] = Field(default_factory=list)

    approval_required: bool = False
    approver_roles: list[str] = Field(default_factory=list)

    legal_review_required: bool | None = None
    legal_rationale: str | None = None

    policy_sources: list[str] = Field(default_factory=list)

    status: WorkflowStatus