from licenseflow_ai.models.customer import Customer
from licenseflow_ai.models.deal import Deal
from licenseflow_ai.models.product import Product
from licenseflow_ai.services.approval_rules import apply_approval_rules

def make_deal(discount_percent: float) -> Deal:
    customer = Customer(
        customer_id = 'CUS-001',
        name = 'Acme Robotics',
        region = 'Europe',
        account_tier = 'Enterprise',
    )

    product = Product(
        product_id = 'PROD-001',
        name = 'EdgeCompute X2',
        category = 'Technology IP',
        base_price = 1_000_000,
    )

    return Deal(
        customer = customer,
        product = product,
        contract_term_years = 3,
        discount_percent = discount_percent,
    )


def test_low_discount_requires_no_approval():
    deal = apply_approval_rules(make_deal(5))

    assert deal.approval_required is False
    assert deal.approvals == []


def test_medium_discount_requires_no_approval():
    deal = apply_approval_rules(make_deal(15))

    assert deal.approval_required is True
    assert deal.approvals[0].approver_role == 'Sales Director'


def test_high_discount_requires_no_approval():
    deal = apply_approval_rules(make_deal(25))

    assert deal.approval_required is True
    assert deal.approvals[0].approver_role == 'VP Sales'
