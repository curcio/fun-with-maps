from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.main as backend

client = TestClient(backend.app)


class TestBackend:
    """Tests for the FastAPI backend."""

    def test_index_returns_random_country(self, mock_world_data):
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
            response = client.get("/")
            assert response.status_code == 200
            assert "United States" in response.text
            assert "Canada" in response.text
            assert "Mexico" in response.text

    def test_country_list_full(self, mock_world_data):
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
            response = client.get("/")
            assert response.status_code == 200
            # datalist should include all countries from the mocked world data
            assert response.text.count("<option value=") == len(mock_world_data)

    def test_submit_endpoint_removed(self):
        response = client.post("/submit", data={"text": "hello"})
        assert response.status_code == 404
