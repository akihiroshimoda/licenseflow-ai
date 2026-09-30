from enum import Enum

from pydantic import BaseModel


class ApprovalStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class Approval(BaseModel):
    approver_role: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: str | None = None

    