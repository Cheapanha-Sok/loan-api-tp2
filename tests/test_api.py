"""Run with: python train.py && pytest -v  (or with MLFLOW_TRACKING_URI set to use the registry)"""
import pytest
from fastapi.testclient import TestClient

from main import APPLICATIONS, app

GOOD = {"amount_usd": 1500, "term_months": 12, "monthly_income_usd": 350.0, "previous_loans": 1, "late_payments": 0}


@pytest.fixture
def client():
    APPLICATIONS.clear()
    with TestClient(app) as c:  # "with" runs the lifespan, so the model is loaded
        yield c


def test_health_reports_model_version(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["model_version"]  # "1.0.0" from the file, or a registry version such as "1"


def test_prediction_is_a_probability(client):
    body = client.post("/api/v1/predictions", json=GOOD).json()
    assert 0 <= body["default_probability"] <= 1
    assert body["risk_band"] in {"low", "medium", "high"}


def test_amount_above_limit_is_rejected(client):
    assert client.post("/api/v1/predictions", json={**GOOD, "amount_usd": 9000}).status_code == 422


def test_create_and_read_application(client):
    created = client.post("/api/v1/applications", json={**GOOD, "borrower_id": 1042})
    assert created.status_code == 201
    app_id = created.json()["id"]
    assert created.headers["location"] == f"/api/v1/applications/{app_id}"  # the contract's Location header
    assert client.get(f"/api/v1/applications/{app_id}").json()["borrower_id"] == 1042


def test_missing_application_is_404(client):
    assert client.get("/api/v1/applications/99999").status_code == 404


def test_health_reports_git_sha(client):
    assert client.get("/health").json()["git_sha"]  # "dev" locally, the commit SHA in production


def test_api_key_required_when_configured(client, monkeypatch):
    monkeypatch.setattr("main.API_KEY", "test-key")
    assert client.get("/health").status_code == 200                       # health stays open
    assert client.get("/api/v1/applications").status_code == 401          # no key
    assert client.get("/api/v1/applications", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/v1/applications", headers={"X-API-Key": "test-key"}).status_code == 200


RISKY = {"amount_usd": 5000, "term_months": 3, "monthly_income_usd": 200.0, "previous_loans": 0, "late_payments": 4}


def test_risky_applicant_scores_higher_than_safe_applicant(client):
    """Bad release drill (Lesson 6.7): an inverted probability passed every other test and went live.
    A risky borrower must score higher than a safe one, and the band must agree with the probability."""
    safe = client.post("/api/v1/predictions", json=GOOD).json()
    risky = client.post("/api/v1/predictions", json=RISKY).json()
    assert risky["default_probability"] > safe["default_probability"]
    assert safe["risk_band"] == "low" and safe["default_probability"] < 0.2
    assert risky["risk_band"] == "high" and risky["default_probability"] >= 0.5
