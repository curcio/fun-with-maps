from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.main as backend

client = TestClient(backend.app)


class TestBackend:
    """Tests for the FastAPI backend."""

    def test_index_served(self):
        response = client.get("/")
        assert response.status_code == 200
        assert '<script src="/static/script.js"></script>' in response.text

    def test_api_new_game(self, mock_world_data):
        with patch.object(
            backend, "fetch_world_map", return_value=mock_world_data
        ), patch.object(
            backend.random, "choice", return_value="United States"
        ), patch.object(
            backend,
            "find_multiple_closest_countries",
            return_value=[("Canada", 1.0), ("Mexico", 2.0)],
        ):
            backend.data_loaded = False
            response = client.get("/api/new-game")
            assert response.status_code == 200
            data = response.json()
            assert data["country"] == "United States"
            assert data["hints"] == ["Canada", "Mexico"]
            assert len(data["valid_countries"]) == len(mock_world_data)

    def test_submit_endpoint_removed(self):
        response = client.post("/submit", data={"text": "hello"})
        assert response.status_code == 404

    def test_api_new_game_no_data(self):
        """Return empty values when no world data is available."""
        with patch.object(backend, "fetch_world_map", return_value=None):
            backend.data_loaded = False
            response = client.get("/api/new-game")
            assert response.status_code == 200
            data = response.json()
            assert data["country"] is None
            assert data["hints"] == []
            assert data["valid_countries"] == []
            assert data["image_path"] is None

    def test_api_new_game_with_image(self, mock_world_data):
        """Ensure image path from helper is included in response."""
        with patch.object(
            backend, "fetch_world_map", return_value=mock_world_data
        ), patch.object(
            backend.random, "choice", return_value="United States"
        ), patch.object(
            backend, "get_country_image_path", return_value="/images/US/test.png"
        ), patch.object(
            backend, "find_multiple_closest_countries", return_value=[("Canada", 1.0)]
        ):
            backend.data_loaded = False
            response = client.get("/api/new-game")
            assert response.status_code == 200
            data = response.json()
            assert data["image_path"] == "/images/US/test.png"
