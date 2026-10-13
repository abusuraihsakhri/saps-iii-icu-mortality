"""API, UI entry point and audit-signature regression tests."""

from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail


client = TestClient(app)


def test_api_mortality_estimate():
    response = client.post("/api/mortality", json={"saps3_score": 50})
    assert response.status_code == 200
    result = response.json()
    assert result["predicted_hospital_mortality_percent"] == 17.35
    assert result["outcome"] == "In-hospital mortality"


def test_api_rejects_invalid_scores():
    for score in (-1, 218, 50.5, "50", True, None):
        response = client.post("/api/mortality", json={"saps3_score": score})
        assert response.status_code == 422


def test_api_homepage_available():
    response = client.get("/")
    assert response.status_code == 200
    assert "SAPS 3 hospital mortality estimator" in response.text
    assert "moralityProbability" not in response.text
    assert "mortalityProbability" in response.text
    assert "fetch(" not in response.text


def test_audit_signature_verification_detects_tampering():
    trail = AuditTrail("test-only-secret")
    trail.log("research", "test", "SCORING", {"status": "ok"})
    trail.log("research", "test", "SCORING", {"status": "ok"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "changed"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "tampered"
    assert not trail.verify_integrity()


def test_audit_signature_verification_detects_rewritten_chain():
    trail = AuditTrail("test-only-secret")
    trail.log("research", "test", "SCORING", {"status": "ok"})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()
