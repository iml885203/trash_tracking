"""Basic import tests to ensure modules can be loaded."""

import pytest


def test_import_trash_tracking_core():
    """Test that trash_tracking_core package can be imported."""
    import trash_tracking_core

    assert trash_tracking_core is not None


def test_import_ntpc_api_client():
    """Test that NTPCApiClient can be imported."""
    from trash_tracking_core.clients.ntpc_api import NTPCApiClient

    assert NTPCApiClient is not None


def test_import_models():
    """Test that data models can be imported."""
    from trash_tracking_core.models.point import Point
    from trash_tracking_core.models.truck import TruckLine

    assert Point is not None
    assert TruckLine is not None


def test_import_geocoder():
    """Test that Geocoder can be imported."""
    from trash_tracking_core.utils.geocoding import Geocoder

    assert Geocoder is not None


def test_import_route_analyzer():
    """Test that RouteAnalyzer can be imported."""
    from trash_tracking_core.utils.route_analyzer import RouteAnalyzer

    assert RouteAnalyzer is not None
