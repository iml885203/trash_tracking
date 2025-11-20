"""
Integration Test Suite 2: API Status Functionality

Tests the Flask API endpoints for garbage truck tracking status.
Requires the Flask app to be running.
"""

import time

import pytest
import requests


class TestAPIStatus:
    """Test Suite 2: API 狀態查詢"""

    BASE_URL = "http://localhost:5000"

    @pytest.fixture(scope="class")
    def api_available(self):
        """Check if API is available before running tests"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("API server is not running. Start with: python3 app.py")

    def test_health_check(self, api_available):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "config" in data
        assert "enter_point" in data["config"]
        assert "exit_point" in data["config"]
        assert "trigger_mode" in data["config"]

    def test_status_endpoint_idle_state(self, api_available):
        """Test status endpoint returns idle when no truck nearby"""
        # Reset tracker first
        reset_response = requests.post(f"{self.BASE_URL}/api/reset", timeout=5)
        assert reset_response.status_code == 200

        # Wait a moment for reset to complete
        time.sleep(1)

        # Query status
        response = requests.get(f"{self.BASE_URL}/api/trash/status", timeout=10)

        assert response.status_code in [200, 503]  # 503 if error, 200 if ok
        data = response.json()

        assert "status" in data
        assert "reason" in data
        assert "timestamp" in data

        # Most likely idle when no truck is actually nearby
        if response.status_code == 200:
            assert data["status"] in ["idle", "nearby"]

    def test_reset_endpoint(self, api_available):
        """Test reset endpoint"""
        response = requests.post(f"{self.BASE_URL}/api/reset", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "reset" in data["message"].lower()
        assert "timestamp" in data

    def test_status_endpoint_structure(self, api_available):
        """Test status endpoint response structure"""
        response = requests.get(f"{self.BASE_URL}/api/trash/status", timeout=10)

        # Should always return valid JSON
        assert response.status_code in [200, 503]
        data = response.json()

        # Required fields
        assert "status" in data
        assert "reason" in data
        assert "timestamp" in data

        # If status is nearby, should have truck info
        if data["status"] == "nearby":
            assert "truck" in data
            assert "line_name" in data["truck"]
            assert "car_no" in data["truck"]

    def test_api_error_handling(self, api_available):
        """Test API error handling for invalid endpoints"""
        response = requests.get(f"{self.BASE_URL}/api/invalid_endpoint", timeout=5)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_concurrent_status_requests(self, api_available):
        """Test API can handle concurrent status requests"""
        import concurrent.futures

        def make_request():
            return requests.get(f"{self.BASE_URL}/api/trash/status", timeout=10)

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code in [200, 503] for r in responses)
        assert all("status" in r.json() for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
