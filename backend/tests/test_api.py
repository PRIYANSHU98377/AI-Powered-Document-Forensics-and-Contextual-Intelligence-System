import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["system"] == "DocDetective"
    assert "disclaimer" in data

def test_audit_verify_empty():
    res = client.get("/api/v1/audit/verify")
    assert res.status_code == 200
    data = res.json()
    assert "is_valid" in data
    assert data["is_valid"] is True

def test_create_and_list_case():
    res = client.post("/api/v1/cases", json={"name": "Test Integration Case", "description": "Testing API"})
    assert res.status_code == 200
    case_data = res.json()
    assert "case_id" in case_data
    case_id = case_data["case_id"]

    list_res = client.get("/api/v1/cases")
    assert list_res.status_code == 200
    cases = list_res.json()
    assert any(c["case_id"] == case_id for c in cases)
