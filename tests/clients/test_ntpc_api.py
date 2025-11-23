"""Tests for NTPC API Client"""
import time
from unittest.mock import MagicMock, patch

import pytest
from trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
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


@pytest.fixture
def sample_multi_line_response():
    """Sample API response with multiple truck lines"""
    return {
        "Line": [
            {
                "LineID": "L001",
                "LineName": "Route A",
                "Area": "Area 1",
                "ArrivalRank": 1,
                "Diff": 0,
                "CarNO": "ABC-1111",
                "Location": "Location A",
                "LocationLat": 25.0,
                "LocationLon": 121.5,
                "BarCode": "001",
                "Point": [
                    {
                        "SourcePointID": 1,
                        "PointName": "Point A1",
                        "PointRank": 1,
                        "PointTime": "18:00",
                        "Lat": 25.0,
                        "Lon": 121.5,
                    }
                ],
            },
            {
                "LineID": "L002",
                "LineName": "Route B",
                "Area": "Area 2",
                "ArrivalRank": 1,
                "Diff": 5,
                "CarNO": "ABC-2222",
                "Location": "Location B",
                "LocationLat": 25.01,
                "LocationLon": 121.51,
                "BarCode": "002",
                "Point": [
                    {
                        "SourcePointID": 2,
                        "PointName": "Point B1",
                        "PointRank": 1,
                        "PointTime": "18:10",
                        "Lat": 25.01,
                        "Lon": 121.51,
                    }
                ],
            },
        ],
        "TimeStamp": "20231123120000",
    }


class TestNTPCApiClientInit:
    """Test NTPC API client initialization"""

    def test_init_default(self):
        """Test initialization with default parameters"""
        client = NTPCApiClient()

        assert client.cache_enabled is True

    def test_init_cache_disabled(self):
        """Test initialization with cache disabled"""
        client = NTPCApiClient(cache_enabled=False)

        assert client.cache_enabled is False

    def test_init_cache_enabled(self):
        """Test initialization with cache explicitly enabled"""
        client = NTPCApiClient(cache_enabled=True)

        assert client.cache_enabled is True


class TestGetAroundPoints:
    """Test getting nearby garbage trucks"""

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_get_around_points_success(self, mock_session, sample_multi_line_response):
        """Test successful API call"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = sample_multi_line_response
        mock_session.return_value.post.return_value = mock_response

        client = NTPCApiClient(cache_enabled=False)
        result = client.get_around_points(25.018, 121.471, 0, None)

        assert len(result) == 2
        assert isinstance(result[0], TruckLine)
        assert isinstance(result[1], TruckLine)
        assert result[0].line_name == "Route A"
        assert result[1].line_name == "Route B"

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_get_around_points_empty_response(self, mock_session):
        """Test API call with empty response"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"Line": [], "TimeStamp": "20231123120000"}
        mock_session.return_value.post.return_value = mock_response

        client = NTPCApiClient(cache_enabled=False)
        result = client.get_around_points(25.018, 121.471, 0, None)

        assert len(result) == 0

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_get_around_points_with_filters(self, mock_session, sample_multi_line_response):
        """Test API call with time and week filters"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = sample_multi_line_response
        mock_session.return_value.post.return_value = mock_response

        client = NTPCApiClient(cache_enabled=False)
        result = client.get_around_points(25.018, 121.471, 30, 1)  # 30 min filter, Monday

        assert len(result) == 2
        # Verify the request was made with correct parameters
        mock_session.return_value.post.assert_called_once()


class TestApiErrorHandling:
    """Test API error handling"""

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_api_timeout(self, mock_session):
        """Test handling of API timeout"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock to raise timeout
        import requests

        mock_session.return_value.post.side_effect = requests.Timeout("Connection timeout")

        client = NTPCApiClient(cache_enabled=False)

        with pytest.raises(NTPCApiError) as exc_info:
            client.get_around_points(25.018, 121.471, 0, None)

        assert "timeout" in str(exc_info.value).lower()

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_api_connection_error(self, mock_session):
        """Test handling of connection error"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock to raise connection error
        import requests

        mock_session.return_value.post.side_effect = requests.ConnectionError("Connection failed")

        client = NTPCApiClient(cache_enabled=False)

        with pytest.raises(NTPCApiError) as exc_info:
            client.get_around_points(25.018, 121.471, 0, None)

        assert "connection" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_api_http_error(self, mock_session):
        """Test handling of HTTP error"""
        # Clear cache first
        NTPCApiClient.clear_cache()

        # Setup mock to raise HTTP error
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error", response=mock_response)
        mock_session.return_value.post.return_value = mock_response

        client = NTPCApiClient(cache_enabled=False)

        with pytest.raises(NTPCApiError):
            client.get_around_points(25.018, 121.471, 0, None)


class TestCacheBasics:
    """Test basic cache functionality"""

    def test_cache_enabled_by_default(self):
        """Test that cache is enabled by default"""
        client = NTPCApiClient()
        assert client.cache_enabled is True

    def test_cache_can_be_disabled(self):
        """Test that cache can be disabled"""
        client = NTPCApiClient(cache_enabled=False)
        assert client.cache_enabled is False

    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = NTPCApiClient._get_cache_key(25.018269, 121.471703, 0, None)
        key2 = NTPCApiClient._get_cache_key(25.018269, 121.471703, 0, None)
        assert key1 == key2

        # Different coordinates should produce different keys
        key3 = NTPCApiClient._get_cache_key(25.019999, 121.471703, 0, None)
        assert key1 != key3

    def test_cache_key_coordinate_rounding(self):
        """Test that nearby coordinates share cache key"""
        # These coordinates differ by less than 11 meters (~0.0001 degrees)
        key1 = NTPCApiClient._get_cache_key(25.0182690, 121.4717030, 0, None)
        key2 = NTPCApiClient._get_cache_key(25.0182695, 121.4717035, 0, None)

        # Should round to same key
        assert key1 == key2


class TestCacheHitAndMiss:
    """Test cache hit and miss behavior"""

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_cache_hit_avoids_api_call(self, mock_session, sample_api_response):
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

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_cache_disabled_makes_api_calls(self, mock_session, sample_api_response):
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


class TestCacheExpiration:
    """Test cache expiration behavior"""

    def test_cache_expiration(self):
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

    def test_clear_cache(self):
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


class TestCacheSharing:
    """Test cache sharing across instances"""

    @patch("trash_tracking_core.clients.ntpc_api.requests.Session")
    def test_cache_shared_across_instances(self, mock_session, sample_api_response):
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
