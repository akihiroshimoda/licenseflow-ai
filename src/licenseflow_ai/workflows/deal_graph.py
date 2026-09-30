from typing import Literal, TypedDict
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from licenseflow_ai.llm.deal_extractor import extract_deal_request
from licenseflow_ai.llm.policy_analyzer import (
    LegalDecision,
    analyse_legal_policy,
)
from licenseflow_ai.models.audit import AuditEvent
from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.deal import Deal
from licenseflow_ai.models.deal_request import DealRequest
from licenseflow_ai.models.product import Product
from licenseflow_ai.models.workflow_result import (
    WorkflowResult,
    WorkflowStatus,
)
from licenseflow_ai.rag.semantic_retriever import semantic_search
from licenseflow_ai.services.approval_rules import apply_approval_rules
from licenseflow_ai.services.audit_logger import log_audit_event
from licenseflow_ai.services.crm_client import (
    get_customer_by_name,
    get_product_by_name,
)


class LicenseFlowState(TypedDict, total=False):
    workflow_id: str
    text: str

    request: DealRequest
    missing_information: list[str]

    customer: Customer
    product: Product

    deal: Deal

    legal_policies: list[dict]
    legal_decision: LegalDecision

    human_decision: str
    human_comment: str

    result: WorkflowResult


# -------------------------------------------------------------------
# 1. Extract structured deal request from natural language
# -------------------------------------------------------------------

def extract_request_node(
    state: LicenseFlowState,
) -> dict:
    workflow_id = state.get(
        "workflow_id",
        str(uuid4()),
    )

    log_audit_event(
        AuditEvent(
            workflow_id=workflow_id,
            event_type="workflow_started",
            actor="system",
            details={
                "input_text": state["text"],
            },
        )
    )

    request = extract_deal_request(
        state["text"]
    )

    log_audit_event(
        AuditEvent(
            workflow_id=workflow_id,
            event_type="deal_request_extracted",
            actor="claude",
            details=request.model_dump(
                mode="json"
            ),
        )
    )

    return {
        "workflow_id": workflow_id,
        "request": request,
    }


# -------------------------------------------------------------------
# 2. Check whether required information is present
# -------------------------------------------------------------------

def check_information_node(
    state: LicenseFlowState,
) -> dict:
    request = state["request"]

    required_fields = [
        "customer_name",
        "product_name",
        "use_case",
        "region",
        "contract_term_years",
        "discount_percent",
    ]

    missing = [
        field
        for field in required_fields
        if getattr(request, field) is None
    ]

    # Internal policy requires commercial rationale
    # for discounts between 10% and 20%.
    if (
        request.discount_percent is not None
        and 10 <= request.discount_percent <= 20
        and request.commercial_rationale is None
    ):
        missing.append(
            "commercial_rationale"
        )

    return {
        "missing_information": missing,
    }


def route_after_information_check(
    state: LicenseFlowState,
) -> Literal[
    "needs_information",
    "retrieve_crm",
]:
    if state["missing_information"]:
        return "needs_information"

    return "retrieve_crm"


def needs_information_node(
    state: LicenseFlowState,
) -> dict:
    result = WorkflowResult(
        request=state["request"],
        missing_information=state[
            "missing_information"
        ],
        status=WorkflowStatus.NEEDS_INFORMATION,
    )

    return {
        "result": result,
    }


# -------------------------------------------------------------------
# 3. Retrieve verified customer and product data from CRM
# -------------------------------------------------------------------

def retrieve_crm_node(
    state: LicenseFlowState,
) -> dict:
    request = state["request"]

    customer = get_customer_by_name(
        request.customer_name
    )

    product = get_product_by_name(
        request.product_name
    )

    log_audit_event(
        AuditEvent(
            workflow_id=state["workflow_id"],
            event_type="crm_data_retrieved",
            actor="system",
            details={
                "customer_id": (
                    customer.customer_id
                ),
                "product_id": (
                    product.product_id
                ),
            },
        )
    )

    return {
        "customer": customer,
        "product": product,
    }


# -------------------------------------------------------------------
# 4. Build internal Deal object
# -------------------------------------------------------------------

def build_deal_node(
    state: LicenseFlowState,
) -> dict:
    request = state["request"]

    deal = Deal(
        customer=state["customer"],
        product=state["product"],
        contract_term_years=(
            request.contract_term_years
        ),
        discount_percent=(
            request.discount_percent
        ),
    )

    return {
        "deal": deal,
    }


# -------------------------------------------------------------------
# 5. Apply deterministic commercial approval rules
# -------------------------------------------------------------------

def approval_rules_node(
    state: LicenseFlowState,
) -> dict:
    deal = apply_approval_rules(
        state["deal"]
    )

    return {
        "deal": deal,
    }


# -------------------------------------------------------------------
# 6. Retrieve relevant internal policies
# -------------------------------------------------------------------

def retrieve_policy_node(
    state: LicenseFlowState,
) -> dict:
    request = state["request"]

    query = (
        "What legal review is required for "
        f"{request.use_case} use in "
        f"{request.region}?"
    )

    policies = semantic_search(
        query,
        top_k=3,
    )

    log_audit_event(
        AuditEvent(
            workflow_id=state["workflow_id"],
            event_type="policy_retrieved",
            actor="system",
            details={
                "query": query,
                "sources": [
                    policy["source"]
                    for policy in policies
                ],
            },
        )
    )

    return {
        "legal_policies": policies,
    }


# -------------------------------------------------------------------
# 7. Ask Claude to analyse only the retrieved policy context
# -------------------------------------------------------------------

def analyse_policy_node(
    state: LicenseFlowState,
) -> dict:
    decision = analyse_legal_policy(
        deal_description=state["text"],
        policy_chunks=state[
            "legal_policies"
        ],
    )

    deal = state["deal"]

    deal.legal_review_required = (
        decision.legal_review_required is True
    )

    return {
        "legal_decision": decision,
        "deal": deal,
    }


def route_after_policy_analysis(
    state: LicenseFlowState,
) -> Literal[
    "manual_review",
    "human_approval",
    "ready_for_processing",
]:
    decision = state["legal_decision"]
    deal = state["deal"]

    # Policy retrieval / interpretation did not provide
    # enough evidence to make a reliable determination.
    if decision.legal_review_required is None:
        return "manual_review"

    # High-impact commercial/legal decisions
    # remain under human authority.
    if (
        deal.approval_required
        or deal.legal_review_required
    ):
        return "human_approval"

    return "ready_for_processing"


# -------------------------------------------------------------------
# Helper: construct final workflow result
# -------------------------------------------------------------------

def build_result(
    state: LicenseFlowState,
    status: WorkflowStatus,
) -> WorkflowResult:
    deal = state["deal"]
    decision = state["legal_decision"]

    policy_sources = list(
        dict.fromkeys(
            policy["source"]
            for policy in state[
                "legal_policies"
            ]
        )
    )

    return WorkflowResult(
        request=state["request"],
        customer=state["customer"],
        product=state["product"],
        approval_required=(
            deal.approval_required
        ),
        approver_roles=[
            approval.approver_role
            for approval in deal.approvals
        ],
        legal_review_required=(
            decision.legal_review_required
        ),
        legal_rationale=(
            decision.rationale
        ),
        policy_sources=policy_sources,
        status=status,
    )


# -------------------------------------------------------------------
# 8A. Manual review
# -------------------------------------------------------------------

def manual_review_node(
    state: LicenseFlowState,
) -> dict:
    return {
        "result": build_result(
            state,
            WorkflowStatus.MANUAL_REVIEW,
        )
    }


# -------------------------------------------------------------------
# 8B. Human-in-the-loop approval
# -------------------------------------------------------------------

def human_approval_node(
    state: LicenseFlowState,
) -> dict:
    deal = state["deal"]
    decision = state["legal_decision"]

    approval_request = {
        "question": (
            "Approve this licensing deal?"
        ),
        "workflow_id": (
            state["workflow_id"]
        ),
        "customer": (
            state["customer"].name
        ),
        "product": (
            state["product"].name
        ),
        "discount_percent": (
            deal.discount_percent
        ),
        "commercial_approvers": [
            approval.approver_role
            for approval in deal.approvals
        ],
        "legal_review_required": (
            decision.legal_review_required
        ),
        "legal_rationale": (
            decision.rationale
        ),
    }

    # LangGraph pauses here until a human
    # resumes the workflow.
    human_response = interrupt(
        approval_request
    )

    if isinstance(
        human_response,
        dict,
    ):
        human_decision = human_response.get(
            "decision",
            "",
        )
        human_comment = human_response.get(
            "comment",
            "",
        )
    else:
        human_decision = str(
            human_response
        )
        human_comment = ""

    human_decision = (
        human_decision
        .strip()
        .lower()
    )

    log_audit_event(
        AuditEvent(
            workflow_id=state["workflow_id"],
            event_type="human_decision",
            actor="human",
            details={
                "decision": human_decision,
                "comment": human_comment,
            },
        )
    )

    return {
        "human_decision": human_decision,
        "human_comment": human_comment,
    }


def route_after_human_approval(
    state: LicenseFlowState,
) -> Literal[
    "approved",
    "rejected",
]:
    if (
        state["human_decision"]
        == "approve"
    ):
        return "approved"

    # Anything other than an explicit
    # "approve" is treated conservatively.
    return "rejected"


# -------------------------------------------------------------------
# 9. Terminal states
# -------------------------------------------------------------------

def approved_node(
    state: LicenseFlowState,
) -> dict:
    return {
        "result": build_result(
            state,
            WorkflowStatus.APPROVED,
        )
    }


def rejected_node(
    state: LicenseFlowState,
) -> dict:
    return {
        "result": build_result(
            state,
            WorkflowStatus.REJECTED,
        )
    }


def ready_for_processing_node(
    state: LicenseFlowState,
) -> dict:
    return {
        "result": build_result(
            state,
            WorkflowStatus.READY_FOR_PROCESSING,
        )
    }


# -------------------------------------------------------------------
# Graph construction
# -------------------------------------------------------------------

builder = StateGraph(
    LicenseFlowState
)


builder.add_node(
    "extract_request",
    extract_request_node,
)

builder.add_node(
    "check_information",
    check_information_node,
)

builder.add_node(
    "needs_information",
    needs_information_node,
)

builder.add_node(
    "retrieve_crm",
    retrieve_crm_node,
)

builder.add_node(
    "build_deal",
    build_deal_node,
)

builder.add_node(
    "approval_rules",
    approval_rules_node,
)

builder.add_node(
    "retrieve_policy",
    retrieve_policy_node,
)

builder.add_node(
    "analyse_policy",
    analyse_policy_node,
)

builder.add_node(
    "manual_review",
    manual_review_node,
)

builder.add_node(
    "human_approval",
    human_approval_node,
)

builder.add_node(
    "approved",
    approved_node,
)

builder.add_node(
    "rejected",
    rejected_node,
)

builder.add_node(
    "ready_for_processing",
    ready_for_processing_node,
)


# -------------------------------------------------------------------
# Graph edges
# -------------------------------------------------------------------

builder.add_edge(
    START,
    "extract_request",
)

builder.add_edge(
    "extract_request",
    "check_information",
)

builder.add_conditional_edges(
    "check_information",
    route_after_information_check,
)

builder.add_edge(
    "needs_information",
    END,
)

builder.add_edge(
    "retrieve_crm",
    "build_deal",
)

builder.add_edge(
    "build_deal",
    "approval_rules",
)

builder.add_edge(
    "approval_rules",
    "retrieve_policy",
)

builder.add_edge(
    "retrieve_policy",
    "analyse_policy",
)

builder.add_conditional_edges(
    "analyse_policy",
    route_after_policy_analysis,
)

builder.add_edge(
    "manual_review",
    END,
)

builder.add_conditional_edges(
    "human_approval",
    route_after_human_approval,
)

builder.add_edge(
    "approved",
    END,
)

builder.add_edge(
    "rejected",
    END,
)

builder.add_edge(
    "ready_for_processing",
    END,
)


# -------------------------------------------------------------------
# Checkpointing
# -------------------------------------------------------------------

checkpointer = InMemorySaver()

deal_graph = builder.compile(
    checkpointer=checkpointer,
)