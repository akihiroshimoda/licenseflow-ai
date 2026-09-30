from licenseflow_ai.models.approval import Approval
from licenseflow_ai.models.deal import Deal, DealStatus

def apply_approval_rules(deal: Deal) -> Deal:
    if deal.discount_percent < 10:
        deal.approval_required = False
        deal.approvals = []
    
    elif deal.discount_percent <= 20:
        deal.approval_required = True
        deal.approvals = [
            Approval(approver_role='Sales Director')
        ]
        deal.status = DealStatus.AWAITING_APPROVAL

    else:
        deal.approval_required = True
        deal.approvals = [
            Approval(approver_role='VP Sales')
        ]

    return deal