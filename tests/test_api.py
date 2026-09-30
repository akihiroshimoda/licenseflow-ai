from fastapi.testclient import TestClient

from licenseflow_ai.api.main import app
from licenseflow_ai.api.dependencies import get_db
from licenseflow_ai.database.models import CustomerDB

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_get_customer():
    response = client.get(
        "/crm/customers",
        params={
            "name": "Acme Robotics"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "CUS-001"
    assert data["name"] == "Acme Robotics"
    assert data["region"] == "Europe"
    assert data["account_tier"] == "Enterprise"


def test_unknown_customer_returns_404():
    response = client.get(
        "/crm/customers",
        params={
            "name": "Does Not Exist"
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Customer not found"
    }