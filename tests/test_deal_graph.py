from langgraph.types import Command

from licenseflow_ai.llm.policy_analyzer import LegalDecision
from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.deal_request import DealRequest
from licenseflow_ai.models.product import Product
from licenseflow_ai.models.workflow_result import WorkflowStatus
import licenseflow_ai.workflows.deal_graph as graph_module


CUSTOMER = Customer(
    customer_id="CUS-001",
    name="Acme Robotics",
    region="Europe",
    account_tier="Enterprise",
)

PRODUCT = Product(
    product_id="PROD-001",
    name="EdgeCompute X2",
    category="Technology IP",
    base_price=1_000_000,
)


def patch_common_dependencies(
    monkeypatch,
    request: DealRequest,
    legal_review_required: bool | None,
):
    """
    Replace external dependencies with deterministic test doubles.

    No Claude API, CRM HTTP request, or embedding model is required.
    """

    monkeypatch.setattr(
        graph_module,
        "extract_deal_request",
        lambda text: request,
    )

    monkeypatch.setattr(
        graph_module,
        "get_customer_by_name",
        lambda name: CUSTOMER,
    )

    monkeypatch.setattr(
        graph_module,
        "get_product_by_name",
        lambda name: PRODUCT,
    )

    monkeypatch.setattr(
        graph_module,
        "semantic_search",
        lambda query, top_k=3: [
            {
                "source": "licensing_policy.md",
                "content": "Relevant licensing policy.",
                "score": 0.9,
            },
            {
                "source": "legal_playbook.md",
                "content": "Relevant legal policy.",
                "score": 0.8,
            },
        ],
    )

    if legal_review_required is True:
        rationale = (
            "Automotive applications require Legal review."
        )
    elif legal_review_required is False:
        rationale = (
            "The retrieved policies do not require Legal review."
        )
    else:
        rationale = (
            "The retrieved policies are insufficient "
            "to determine whether Legal review is required."
        )

    monkeypatch.setattr(
        graph_module,
        "analyse_legal_policy",
        lambda deal_description, policy_chunks: LegalDecision(
            legal_review_required=legal_review_required,
            rationale=rationale,
        ),
    )

    # Avoid writing test events into the real audit log.
    monkeypatch.setattr(
        graph_module,
        "log_audit_event",
        lambda event: None,
    )


def test_standard_deal_ready_for_processing(
    monkeypatch,
):
    request = DealRequest(
        customer_name="Acme Robotics",
        product_name="EdgeCompute X2",
        use_case="industrial device",
        region="Europe",
        contract_term_years=3,
        discount_percent=5,
        commercial_rationale=None,
    )

    patch_common_dependencies(
        monkeypatch,
        request=request,
        legal_review_required=False,
    )

    config = {
        "configurable": {
            "thread_id": "test-standard-deal"
        }
    }

    output = graph_module.deal_graph.invoke(
        {
            "text": "Standard 5 percent deal."
        },
        config=config,
    )

    result = output["result"]

    assert (
        result.status
        == WorkflowStatus.READY_FOR_PROCESSING
    )
    assert result.approval_required is False
    assert result.legal_review_required is False
    assert result.approver_roles == []


def test_automotive_deal_requires_sales_director_and_legal(
    monkeypatch,
):
    request = DealRequest(
        customer_name="Acme Robotics",
        product_name="EdgeCompute X2",
        use_case="automotive",
        region="Europe",
        contract_term_years=3,
        discount_percent=15,
        commercial_rationale=(
            "Strategic customer with multi-year commitment."
        ),
    )

    patch_common_dependencies(
        monkeypatch,
        request=request,
        legal_review_required=True,
    )

    config = {
        "configurable": {
            "thread_id": "test-automotive-deal"
        }
    }

    output = graph_module.deal_graph.invoke(
        {
            "text": "Automotive deal with 15 percent discount."
        },
        config=config,
    )

    assert "__interrupt__" in output

    result_output = graph_module.deal_graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "comment": "Approved for test.",
            }
        ),
        config=config,
    )

    result = result_output["result"]

    assert result.status == WorkflowStatus.APPROVED
    assert result.approval_required is True
    assert result.legal_review_required is True
    assert "Sales Director" in result.approver_roles


def test_high_discount_requires_vp_sales(
    monkeypatch,
):
    request = DealRequest(
        customer_name="Acme Robotics",
        product_name="EdgeCompute X2",
        use_case="industrial device",
        region="Europe",
        contract_term_years=3,
        discount_percent=25,
        commercial_rationale=(
            "Strategic expansion opportunity."
        ),
    )

    patch_common_dependencies(
        monkeypatch,
        request=request,
        legal_review_required=False,
    )

    config = {
        "configurable": {
            "thread_id": "test-high-discount"
        }
    }

    output = graph_module.deal_graph.invoke(
        {
            "text": "Deal with 25 percent discount."
        },
        config=config,
    )

    assert "__interrupt__" in output

    result_output = graph_module.deal_graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "comment": "VP approval granted.",
            }
        ),
        config=config,
    )

    result = result_output["result"]

    assert result.status == WorkflowStatus.APPROVED
    assert result.approval_required is True
    assert "VP Sales" in result.approver_roles
    assert result.legal_review_required is False


def test_missing_information_stops_workflow(
    monkeypatch,
):
    request = DealRequest(
        customer_name="Acme Robotics",
        product_name="EdgeCompute X2",
        use_case="automotive",
        region="Europe",
        contract_term_years=None,
        discount_percent=15,
        commercial_rationale=None,
    )

    patch_common_dependencies(
        monkeypatch,
        request=request,
        legal_review_required=True,
    )

    config = {
        "configurable": {
            "thread_id": "test-missing-information"
        }
    }

    output = graph_module.deal_graph.invoke(
        {
            "text": "Incomplete licensing request."
        },
        config=config,
    )

    result = output["result"]

    assert (
        result.status
        == WorkflowStatus.NEEDS_INFORMATION
    )

    assert (
        "contract_term_years"
        in result.missing_information
    )

    assert (
        "commercial_rationale"
        in result.missing_information
    )


def test_uncertain_policy_routes_to_manual_review(
    monkeypatch,
):
    request = DealRequest(
        customer_name="Acme Robotics",
        product_name="EdgeCompute X2",
        use_case="experimental research",
        region="Europe",
        contract_term_years=2,
        discount_percent=5,
        commercial_rationale=None,
    )

    patch_common_dependencies(
        monkeypatch,
        request=request,
        legal_review_required=None,
    )

    config = {
        "configurable": {
            "thread_id": "test-manual-review"
        }
    }

    output = graph_module.deal_graph.invoke(
        {
            "text": "Unusual experimental licensing request."
        },
        config=config,
    )

    result = output["result"]

    assert (
        result.status
        == WorkflowStatus.MANUAL_REVIEW
    )

    assert result.legal_review_required is None