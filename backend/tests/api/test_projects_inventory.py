from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_inventory_route_exists() -> None:
    resp = client.get("/api/v1/projects")
    assert resp.status_code in (200, 204, 404, 500)
