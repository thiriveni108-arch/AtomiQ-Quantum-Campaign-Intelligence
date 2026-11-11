from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_official_web_api_uses_real_artifacts():
    data = client.get("/api/official/overview").json()
    assert data["validation"]["official_ready"] is True
    assert len(data["top10"]) == 10 and len(data["selected"]) == 6
    assert data["model"]["depth"] == 1

def test_sandbox_is_explicit_and_recomputes_exact_solution():
    response = client.post("/api/sandbox/optimize", json={"budget":25,"capacity":22,"qaoa_depth":2,"seed":42,"shots":128})
    data = response.json()
    assert response.status_code == 200 and data["mode"] == "sandbox"
    assert data["exact"]["best"]["objective"] > 0
    assert data["qaoa_source"] == "saved official run"

def test_visualization_endpoints_are_real_and_complete():
    feature = client.get("/api/models/feature-space").json()
    landscape = client.get("/api/stage2/landscape").json()
    assert len(feature["points"]) == 300 and feature["dimensions"] == 4
    assert len(landscape["records"]) == 210
    assert abs(landscape["best"]["objective"] - 45.041981731448715) < 1e-12
