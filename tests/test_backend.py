from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestBackend:
    """Tests for the FastAPI backend."""

    def test_index_and_submit(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "<form" in response.text

        post_response = client.post("/submit", data={"text": "hello"})
        assert post_response.status_code == 200
        assert "You submitted: hello" in post_response.text
