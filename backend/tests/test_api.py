import os

os.environ["DATABASE_URL"] = "sqlite:///./test-fraudstream.db"

from app.main import app
from fastapi.testclient import TestClient


def test_health_and_demo_token():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        login = client.post("/api/auth/demo")
        assert login.status_code == 200
        assert login.json()["token_type"] == "bearer"
        assert login.json()["access_token"]
