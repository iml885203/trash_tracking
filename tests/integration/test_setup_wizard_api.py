"""
Integration Test Suite 3: Setup Wizard API Functionality

Tests the setup wizard web UI and API endpoints.
Requires the Flask app to be running.
"""

import pytest
import requests


class TestSetupWizardAPI:
    """Test Suite 3: 設定精靈 API"""

    BASE_URL = "http://localhost:5000"

    @pytest.fixture(scope="class")
    def api_available(self):
        """Check if API is available before running tests"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("API server is not running. Start with: python3 app.py")

    def test_setup_wizard_homepage(self, api_available):
        """Test setup wizard homepage loads correctly"""
        response = requests.get(f"{self.BASE_URL}/", timeout=5)

        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        assert "設定精靈" in response.text
        assert "垃圾車追蹤系統" in response.text

    def test_setup_route_loads(self, api_available):
        """Test /setup route loads the same page"""
        response = requests.get(f"{self.BASE_URL}/setup", timeout=5)

        assert response.status_code == 200
        assert "設定精靈" in response.text

    def test_suggest_api_with_valid_address(self, api_available):
        """Test auto-suggest API with valid address"""
        response = requests.post(
            f"{self.BASE_URL}/api/setup/suggest",
            json={"address": "新北市板橋區中山路一段161號"},
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "success" in data
        assert data["success"] is True
        assert "recommendation" in data
        assert "config" in data

        # Check recommendation structure
        rec = data["recommendation"]
        assert "latitude" in rec
        assert "longitude" in rec
        assert "route_selection" in rec
        assert "threshold" in rec
        assert "trigger_mode" in rec

        # Check route selection
        route_sel = rec["route_selection"]
        assert "vehicle_number" in route_sel
        assert "route_names" in route_sel
        assert isinstance(route_sel["route_names"], list)
        assert len(route_sel["route_names"]) > 0

        # Check best route
        assert "best_route" in route_sel
        best = route_sel["best_route"]
        assert "line_name" in best
        assert "car_no" in best
        assert "enter_point" in best
        assert "exit_point" in best
        assert "point_name" in best["enter_point"]
        assert "point_name" in best["exit_point"]

    def test_suggest_api_without_address(self, api_available):
        """Test suggest API error handling when address is missing"""
        response = requests.post(
            f"{self.BASE_URL}/api/setup/suggest",
            json={},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_suggest_api_with_invalid_address(self, api_available):
        """Test suggest API with invalid address"""
        response = requests.post(
            f"{self.BASE_URL}/api/setup/suggest",
            json={"address": "Invalid Address 12345"},
            timeout=30,
        )

        # Should return error
        assert response.status_code in [400, 404, 500]
        data = response.json()
        assert "error" in data

    def test_save_api_with_valid_config(self, api_available):
        """Test save configuration API"""
        # First get a valid config from suggest
        suggest_response = requests.post(
            f"{self.BASE_URL}/api/setup/suggest",
            json={"address": "新北市板橋區中山路一段161號"},
            timeout=30,
        )

        if suggest_response.status_code == 200:
            suggest_data = suggest_response.json()

            # Now test save API
            save_response = requests.post(
                f"{self.BASE_URL}/api/setup/save",
                json=suggest_data,
                timeout=10,
            )

            assert save_response.status_code == 200
            save_data = save_response.json()

            assert "success" in save_data
            assert save_data["success"] is True
            assert "message" in save_data
            assert "config_path" in save_data

    def test_save_api_without_config(self, api_available):
        """Test save API error handling when config is missing"""
        response = requests.post(
            f"{self.BASE_URL}/api/setup/save",
            json={},
            timeout=10,
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_setup_wizard_ui_elements(self, api_available):
        """Test that setup wizard UI contains required elements"""
        response = requests.get(f"{self.BASE_URL}/", timeout=5)

        assert response.status_code == 200
        html = response.text

        # Check for key UI elements
        assert "address" in html  # Address input field
        assert "analyzeAddress" in html  # JavaScript function
        assert "saveConfig" in html  # JavaScript function
        assert "progress-step" in html  # Progress indicator

    def test_suggest_api_response_contains_config(self, api_available):
        """Test that suggest API response includes full config object"""
        response = requests.post(
            f"{self.BASE_URL}/api/setup/suggest",
            json={"address": "新北市板橋區中山路一段161號"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            config = data.get("config", {})

            # Check config structure
            assert "location" in config
            assert "tracking" in config
            assert "system" in config

            # Check location
            assert "lat" in config["location"]
            assert "lng" in config["location"]

            # Check tracking
            tracking = config["tracking"]
            assert "target_lines" in tracking
            assert "enter_point" in tracking
            assert "exit_point" in tracking
            assert "trigger_mode" in tracking
            assert "approaching_threshold" in tracking


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
