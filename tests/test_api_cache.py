"""Test API caching functionality"""
import time
from unittest.mock import MagicMock, patch

import pytest
from trash_tracking_core.clients.ntpc_api import NTPCApiClient
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_api_response():
    """Sample API response data"""
    return {
        "Line": [
            {
                "LineName": "A12路線晚上",
                "Car": "ABC-1234",
                "Point": [
                    {
                        "PointName": "測試點1",
                        "Rank": "1",
                        "Time": "18:00",
                        "Latitude": 25.0,
                        "Longitude": 121.5,
                    }
                ],
            }
        ],
        "TimeStamp": "20231123120000",
    }


def test_cache_enabled_by_default():
    """Test that cache is enabled by default"""
    client = NTPCApiClient()
    assert client.cache_enabled is True


def test_cache_can_be_disabled():
    """Test that cache can be disabled"""
    client = NTPCApiClient(cache_enabled=False)
    assert client.cache_enabled is False


def test_cache_key_generation():
    """Test cache key generation"""
    key1 = NTPCApiClient._get_cache_key(25.018269, 121.471703, 0, None)
    key2 = NTPCApiClient._get_cache_key(25.018269, 121.471703, 0, None)
    assert key1 == key2

    # Different coordinates should produce different keys
    key3 = NTPCApiClient._get_cache_key(25.019999, 121.471703, 0, None)
    assert key1 != key3


def test_cache_key_coordinate_rounding():
    """Test that nearby coordinates share cache key"""
    # These coordinates differ by less than 11 meters (~0.0001 degrees)
    key1 = NTPCApiClient._get_cache_key(25.0182690, 121.4717030, 0, None)
    key2 = NTPCApiClient._get_cache_key(25.0182695, 121.4717035, 0, None)

    # Should round to same key
    assert key1 == key2


@patch('trash_tracking_core.clients.ntpc_api.requests.Session')
def test_cache_hit_avoids_api_call(mock_session, sample_api_response):
    """Test that cache hit avoids making API call"""
    # Clear cache first
    NTPCApiClient.clear_cache()

    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = sample_api_response
    mock_session.return_value.post.return_value = mock_response

    client = NTPCApiClient(cache_enabled=True)

    # First call - should hit API
    result1 = client.get_around_points(25.018, 121.471, 0, None)
    assert len(result1) == 1
    assert mock_session.return_value.post.call_count == 1

    # Second call with same params - should use cache
    result2 = client.get_around_points(25.018, 121.471, 0, None)
    assert len(result2) == 1
    assert mock_session.return_value.post.call_count == 1  # Still 1, not 2!

    # Results should be identical
    assert result1[0].line_name == result2[0].line_name


@patch('trash_tracking_core.clients.ntpc_api.requests.Session')
def test_cache_disabled_makes_api_calls(mock_session, sample_api_response):
    """Test that disabled cache always makes API calls"""
    # Clear cache first
    NTPCApiClient.clear_cache()

    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = sample_api_response
    mock_session.return_value.post.return_value = mock_response

    client = NTPCApiClient(cache_enabled=False)

    # First call
    result1 = client.get_around_points(25.018, 121.471, 0, None)
    assert len(result1) == 1
    assert mock_session.return_value.post.call_count == 1

    # Second call - should still hit API
    result2 = client.get_around_points(25.018, 121.471, 0, None)
    assert len(result2) == 1
    assert mock_session.return_value.post.call_count == 2  # Called twice!


def test_cache_expiration():
    """Test that cache expires after TTL"""
    # Clear cache and set short TTL
    NTPCApiClient.clear_cache()
    original_ttl = NTPCApiClient._cache_ttl
    NTPCApiClient._cache_ttl = 1  # 1 second

    try:
        # Put data in cache
        cache_key = "test_key"
        test_data = []  # Use empty list for simplicity
        NTPCApiClient._put_in_cache(cache_key, test_data)

        # Should be in cache
        cached = NTPCApiClient._get_from_cache(cache_key)
        assert cached is not None

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        cached = NTPCApiClient._get_from_cache(cache_key)
        assert cached is None

    finally:
        # Restore original TTL
        NTPCApiClient._cache_ttl = original_ttl
        NTPCApiClient.clear_cache()


def test_clear_cache():
    """Test cache clearing"""
    NTPCApiClient.clear_cache()

    # Add some data
    cache_key = "test_key"
    test_data = []  # Use empty list for simplicity
    NTPCApiClient._put_in_cache(cache_key, test_data)

    # Verify it's there
    assert NTPCApiClient._get_from_cache(cache_key) is not None

    # Clear cache
    NTPCApiClient.clear_cache()

    # Should be gone
    assert NTPCApiClient._get_from_cache(cache_key) is None


@patch('trash_tracking_core.clients.ntpc_api.requests.Session')
def test_cache_shared_across_instances(mock_session, sample_api_response):
    """Test that cache is shared across different client instances"""
    # Clear cache first
    NTPCApiClient.clear_cache()

    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = sample_api_response
    mock_session.return_value.post.return_value = mock_response

    # Create two different client instances
    client1 = NTPCApiClient(cache_enabled=True)
    client2 = NTPCApiClient(cache_enabled=True)

    # Client 1 makes call
    result1 = client1.get_around_points(25.018, 121.471, 0, None)
    assert len(result1) == 1
    assert mock_session.return_value.post.call_count == 1

    # Client 2 makes same call - should use cache from client1
    result2 = client2.get_around_points(25.018, 121.471, 0, None)
    assert len(result2) == 1
    assert mock_session.return_value.post.call_count == 1  # Still 1!
