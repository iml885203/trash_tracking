"""Behave environment configuration"""

import os
import sys
from unittest.mock import MagicMock, patch

from features.fixtures import MOCK_ADDRESSES, create_mock_truck_lines


def before_all(context):
    """Setup before all scenarios"""
    context.use_mocks = os.getenv("USE_MOCK_API", "true").lower() == "true"

    # Mock Home Assistant modules for integration tests
    setup_homeassistant_mocks()

    if context.use_mocks:
        # Setup mock patches
        context.mock_patches = []
        setup_mocks(context)


def before_scenario(context, scenario):
    """Setup before each scenario"""
    # Check if scenario uses real API
    if "real_api" in scenario.effective_tags:
        # Disable mocks for this scenario
        context.use_mocks = False
        if hasattr(context, "mock_patches"):
            for mock_patch in context.mock_patches:
                mock_patch.stop()
            context.mock_patches = []


def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    pass


def after_all(context):
    """Cleanup after all scenarios"""
    if hasattr(context, "mock_patches"):
        for mock_patch in context.mock_patches:
            mock_patch.stop()


def setup_homeassistant_mocks():
    """Mock Home Assistant modules for integration import tests"""
    # Create mock homeassistant module structure
    if "homeassistant" not in sys.modules:
        homeassistant = MagicMock()
        homeassistant.helpers = MagicMock()
        homeassistant.helpers.update_coordinator = MagicMock()
        homeassistant.helpers.entity = MagicMock()
        homeassistant.config_entries = MagicMock()
        homeassistant.core = MagicMock()
        homeassistant.const = MagicMock()
        homeassistant.data_entry_flow = MagicMock()

        # Add to sys.modules so imports will find them
        sys.modules["homeassistant"] = homeassistant
        sys.modules["homeassistant.helpers"] = homeassistant.helpers
        sys.modules["homeassistant.helpers.update_coordinator"] = homeassistant.helpers.update_coordinator
        sys.modules["homeassistant.helpers.entity"] = homeassistant.helpers.entity
        sys.modules["homeassistant.config_entries"] = homeassistant.config_entries
        sys.modules["homeassistant.core"] = homeassistant.core
        sys.modules["homeassistant.const"] = homeassistant.const
        sys.modules["homeassistant.data_entry_flow"] = homeassistant.data_entry_flow


def setup_mocks(context):
    """Setup mock API responses"""

    # Mock NTPCApiClient.get_around_points
    def mock_get_around_points(self, lat, lng, time_filter=0, week=1, dist=1000):
        """Return mock truck lines"""
        return create_mock_truck_lines(count=3)

    ntpc_patch = patch(
        "trash_tracking_core.clients.ntpc_api.NTPCApiClient.get_around_points",
        mock_get_around_points,
    )
    ntpc_patch.start()
    context.mock_patches.append(ntpc_patch)

    # Mock Geocoder.address_to_coordinates
    def mock_address_to_coordinates(self, address, timeout=10):
        """Return mock coordinates for known addresses"""
        if address in MOCK_ADDRESSES:
            return MOCK_ADDRESSES[address]

        # Try to find a match with simplified address
        for mock_addr, coords in MOCK_ADDRESSES.items():
            if address in mock_addr or mock_addr in address:
                return coords

        # Raise error for unknown addresses
        from trash_tracking_core.utils.geocoding import GeocodingError

        raise GeocodingError(f"Unknown address: {address}")

    geocoder_patch = patch(
        "trash_tracking_core.utils.geocoding.Geocoder.address_to_coordinates",
        mock_address_to_coordinates,
    )
    geocoder_patch.start()
    context.mock_patches.append(geocoder_patch)
