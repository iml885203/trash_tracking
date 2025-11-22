"""Behave environment configuration"""

import os
from unittest.mock import patch

import requests

from features.fixtures import MOCK_ADDRESSES, create_mock_truck_lines


def before_all(context):
    """Setup before all scenarios"""
    context.base_url = "http://localhost:5000"
    context.use_mocks = os.getenv("USE_MOCK_API", "true").lower() == "true"

    if context.use_mocks:
        # Setup mock patches
        context.mock_patches = []
        setup_mocks(context)


def before_scenario(context, scenario):
    """Setup before each scenario"""
    # Check if API is needed for this scenario
    if "API" in scenario.feature.name or "設定精靈" in scenario.feature.name:
        try:
            response = requests.get(f"{context.base_url}/health", timeout=5)
            if response.status_code != 200:
                scenario.skip("API server is not running")
        except requests.exceptions.RequestException:
            scenario.skip("API server is not running. Start with: python3 app.py")


def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    pass


def after_all(context):
    """Cleanup after all scenarios"""
    if hasattr(context, "mock_patches"):
        for mock_patch in context.mock_patches:
            mock_patch.stop()


def setup_mocks(context):
    """Setup mock API responses"""

    # Mock NTPCApiClient.get_around_points
    def mock_get_around_points(self, lat, lng, dist):
        """Return mock truck lines"""
        return create_mock_truck_lines(count=3)

    ntpc_patch = patch(
        "trash_tracking_core.clients.ntpc_api.NTPCApiClient.get_around_points",
        mock_get_around_points,
    )
    ntpc_patch.start()
    context.mock_patches.append(ntpc_patch)

    # Mock Geocoder.geocode
    def mock_geocode(self, address):
        """Return mock coordinates for known addresses"""
        if address in MOCK_ADDRESSES:
            return MOCK_ADDRESSES[address]

        # Try to find a match with simplified address
        for mock_addr, coords in MOCK_ADDRESSES.items():
            if address in mock_addr or mock_addr in address:
                return coords

        # Return coordinates for 板橋區 as default
        return MOCK_ADDRESSES["新北市板橋區中山路一段161號"]

    geocoder_patch = patch(
        "trash_tracking_core.utils.geocoding.Geocoder.geocode",
        mock_geocode,
    )
    geocoder_patch.start()
    context.mock_patches.append(geocoder_patch)
