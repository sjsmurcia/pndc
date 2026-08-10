from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde():
    r = cliente.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_openapi_se_genera():
    r = cliente.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/v1/health" in r.json()["paths"]
