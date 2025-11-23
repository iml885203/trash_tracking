"""Tests for Geocoding Utilities"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from trash_tracking_core.utils.geocoding import (
    Geocoder,
    GeocodingError,
    get_current_location_from_address,
)


@pytest.fixture
def geocoder():
    """Geocoder instance for testing"""
    return Geocoder()


@pytest.fixture
def nlsc_response():
    """Sample NLSC API response"""
    return [
        {
            "x": 250000.0,  # TWD97 coordinates
            "y": 2770000.0,
        }
    ]


@pytest.fixture
def nominatim_response():
    """Sample Nominatim API response"""
    return [
        {
            "lat": "25.018269",
            "lon": "121.471703",
        }
    ]


@pytest.fixture
def tgos_response():
    """Sample TGOS API response"""
    return {
        "AddressList": [
            {
                "X": 250000.0,  # TWD97 coordinates
                "Y": 2770000.0,
            }
        ]
    }


class TestGeocoderInit:
    """Test Geocoder initialization"""

    def test_init_default(self):
        """Test initialization with default parameters"""
        geocoder = Geocoder()

        assert geocoder.base_url == "https://api.nlsc.gov.tw/other/TownVillagePointQuery"


class TestCleanAddress:
    """Test address cleaning functionality"""

    def test_clean_address_removes_whitespace(self, geocoder):
        """Test that whitespace is removed"""
        address = "新北市 板橋區 民生路 二段 80號"
        cleaned = geocoder._clean_address(address)

        assert " " not in cleaned
        assert cleaned == "新北市板橋區民生路二段80號"

    def test_clean_address_adds_default_city(self, geocoder):
        """Test that default city is added when missing"""
        address = "板橋區民生路二段80號"
        cleaned = geocoder._clean_address(address)

        assert cleaned.startswith("新北市")
        assert cleaned == "新北市板橋區民生路二段80號"

    def test_clean_address_preserves_existing_city(self, geocoder):
        """Test that existing city is preserved"""
        address = "台北市信義區市府路1號"
        cleaned = geocoder._clean_address(address)

        assert cleaned.startswith("台北市")
        assert "新北市" not in cleaned

    def test_clean_address_with_taipei_traditional(self, geocoder):
        """Test address with traditional Taipei character"""
        address = "臺北市中正區重慶南路1段122號"
        cleaned = geocoder._clean_address(address)

        assert cleaned.startswith("臺北市")
        assert "新北市" not in cleaned

    def test_clean_address_with_taoyuan(self, geocoder):
        """Test address with Taoyuan city"""
        address = "桃園市中壢區中華路一段450號"
        cleaned = geocoder._clean_address(address)

        assert cleaned.startswith("桃園市")
        assert "新北市" not in cleaned

    def test_clean_address_already_has_city_prefix(self, geocoder):
        """Test address that already has city in first 3 characters"""
        address = "市中山區南京東路"
        cleaned = geocoder._clean_address(address)

        # Should not add 新北市 because '市' is in first 3 chars
        assert cleaned == "市中山區南京東路"


class TestSimplifyAddress:
    """Test address simplification functionality"""

    def test_simplify_address_removes_number(self, geocoder):
        """Test simplification removes building number"""
        address = "新北市板橋區民生路二段80號"
        simplified = geocoder._simplify_address(address)

        assert simplified == "新北市板橋區民生路二段"
        assert "80號" not in simplified

    def test_simplify_address_removes_lane(self, geocoder):
        """Test simplification removes lane number"""
        address = "新北市板橋區民生路二段123巷"
        simplified = geocoder._simplify_address(address)

        assert simplified == "新北市板橋區民生路二段"
        assert "123巷" not in simplified

    def test_simplify_address_removes_alley(self, geocoder):
        """Test simplification removes alley number"""
        address = "新北市板橋區民生路二段123巷45弄"
        simplified = geocoder._simplify_address(address)

        assert simplified == "新北市板橋區民生路二段123巷"
        assert "45弄" not in simplified

    def test_simplify_address_removes_section(self, geocoder):
        """Test simplification removes section number"""
        address = "新北市板橋區民生路2段"
        simplified = geocoder._simplify_address(address)

        assert simplified == "新北市板橋區民生路"
        assert "2段" not in simplified

    def test_simplify_address_hierarchy(self, geocoder):
        """Test that simplification follows correct hierarchy (號 before 弄 before 巷 before 段)"""
        # Full address
        address = "新北市板橋區民生路2段123巷45弄67號"

        # First simplification removes 號
        result1 = geocoder._simplify_address(address)
        assert result1 == "新北市板橋區民生路2段123巷45弄"

        # Second simplification removes 弄
        result2 = geocoder._simplify_address(result1)
        assert result2 == "新北市板橋區民生路2段123巷"

        # Third simplification removes 巷
        result3 = geocoder._simplify_address(result2)
        assert result3 == "新北市板橋區民生路2段"

        # Fourth simplification removes 段
        result4 = geocoder._simplify_address(result3)
        assert result4 == "新北市板橋區民生路"

    def test_simplify_address_no_change_when_basic(self, geocoder):
        """Test that basic address returns unchanged"""
        address = "新北市板橋區民生路"
        simplified = geocoder._simplify_address(address)

        assert simplified == address


class TestQueryNLSC:
    """Test NLSC API query"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_success(self, mock_get, geocoder, nlsc_response):
        """Test successful NLSC API query"""
        mock_response = MagicMock()
        mock_response.json.return_value = nlsc_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=10)

        assert result is not None
        assert len(result) == 2
        lat, lng = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        # Verify coordinates are in reasonable range for Taiwan
        assert 21 < lat < 26
        assert 119 < lng < 122

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_empty_response(self, mock_get, geocoder):
        """Test NLSC API with empty response"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_nlsc("Invalid Address", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_zero_coordinates(self, mock_get, geocoder):
        """Test NLSC API with zero coordinates (invalid)"""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"x": 0, "y": 0}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_http_error(self, mock_get, geocoder):
        """Test NLSC API with HTTP error"""
        mock_get.side_effect = requests.HTTPError("500 Server Error")

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_timeout(self, mock_get, geocoder):
        """Test NLSC API with timeout"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nlsc_connection_error(self, mock_get, geocoder):
        """Test NLSC API with connection error"""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=10)

        assert result is None


class TestQueryNominatim:
    """Test Nominatim API query"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_success(self, mock_get, geocoder, nominatim_response):
        """Test successful Nominatim API query"""
        mock_response = MagicMock()
        mock_response.json.return_value = nominatim_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=10)

        assert result is not None
        assert len(result) == 2
        lat, lng = result
        assert lat == 25.018269
        assert lng == 121.471703

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_empty_response(self, mock_get, geocoder):
        """Test Nominatim API with empty response"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_nominatim("Invalid Address", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_user_agent(self, mock_get, geocoder, nominatim_response):
        """Test that Nominatim API includes user agent"""
        mock_response = MagicMock()
        mock_response.json.return_value = nominatim_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=10)

        # Verify User-Agent header is set
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "User-Agent" in call_kwargs["headers"]
        assert call_kwargs["headers"]["User-Agent"] == "TrashTrackingSystem/1.0"

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_country_filter(self, mock_get, geocoder, nominatim_response):
        """Test that Nominatim API filters by Taiwan country code"""
        mock_response = MagicMock()
        mock_response.json.return_value = nominatim_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=10)

        # Verify countrycodes parameter is set to 'tw'
        call_kwargs = mock_get.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"]["countrycodes"] == "tw"

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_http_error(self, mock_get, geocoder):
        """Test Nominatim API with HTTP error"""
        mock_get.side_effect = requests.HTTPError("500 Server Error")

        result = geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_nominatim_timeout(self, mock_get, geocoder):
        """Test Nominatim API with timeout"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=10)

        assert result is None


class TestQueryTGOS:
    """Test TGOS API query"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_success(self, mock_get, geocoder, tgos_response):
        """Test successful TGOS API query"""
        mock_response = MagicMock()
        mock_response.json.return_value = tgos_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=10)

        assert result is not None
        assert len(result) == 2
        lat, lng = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        # Verify coordinates are in reasonable range for Taiwan
        assert 21 < lat < 26
        assert 119 < lng < 122

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_empty_address_list(self, mock_get, geocoder):
        """Test TGOS API with empty address list"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"AddressList": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_tgos("Invalid Address", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_missing_coordinates(self, mock_get, geocoder):
        """Test TGOS API with missing coordinates"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"AddressList": [{"X": None, "Y": None}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_invalid_response_format(self, mock_get, geocoder):
        """Test TGOS API with invalid response format"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Invalid": "Format"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_http_error(self, mock_get, geocoder):
        """Test TGOS API with HTTP error"""
        mock_get.side_effect = requests.HTTPError("500 Server Error")

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_query_tgos_timeout(self, mock_get, geocoder):
        """Test TGOS API with timeout"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=10)

        assert result is None


class TestCoordinateConversion:
    """Test TWD97 to WGS84 coordinate conversion"""

    def test_twd97_to_wgs84_conversion(self, geocoder):
        """Test TWD97 to WGS84 coordinate conversion"""
        # TWD97 coordinates for a location in Taipei area
        x = 250000.0
        y = 2770000.0

        lat, lng = geocoder._twd97_to_wgs84(x, y)

        # Verify results are in WGS84 range for Taiwan
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        assert 21 < lat < 26  # Taiwan latitude range
        assert 119 < lng < 122  # Taiwan longitude range

    def test_twd97_to_wgs84_zero_offset(self, geocoder):
        """Test TWD97 to WGS84 with zero offset (base point)"""
        # Coordinates at the central meridian
        x = 250000.0  # At the false easting
        y = 0.0

        lat, lng = geocoder._twd97_to_wgs84(x, y)

        # Should be near the equator and central meridian (121°E)
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        assert abs(lng - 121.0) < 1.0  # Should be close to 121°E


class TestTrySimplifiedAddresses:
    """Test progressive address simplification"""

    @patch.object(Geocoder, "_query_nominatim")
    def test_try_simplified_addresses_first_level(self, mock_query, geocoder):
        """Test that first simplification succeeds"""
        # First call (simplified once: 新北市板橋區民生路二段) returns data
        mock_query.return_value = (25.018269, 121.471703)

        result = geocoder._try_simplified_addresses("新北市板橋區民生路二段80號", timeout=10)

        assert result is not None
        assert len(result) == 2
        assert result == (25.018269, 121.471703)
        # Should have been called once with the simplified address
        assert mock_query.call_count == 1

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_try_simplified_addresses_multiple_levels(self, mock_get, geocoder, nominatim_response):
        """Test multiple levels of simplification"""
        mock_response = MagicMock()
        # Empty responses until the third try
        mock_response.json.side_effect = [[], [], nominatim_response]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._try_simplified_addresses("新北市板橋區民生路二段123巷45弄67號", timeout=10)

        assert result is not None
        assert len(result) == 2

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_try_simplified_addresses_all_fail(self, mock_get, geocoder):
        """Test when all simplification attempts fail"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder._try_simplified_addresses("新北市板橋區民生路二段80號", timeout=10)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_try_simplified_addresses_stops_when_no_change(self, mock_get, geocoder):
        """Test that simplification stops when address cannot be simplified further"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Basic address that cannot be simplified
        result = geocoder._try_simplified_addresses("新北市板橋區", timeout=10)

        assert result is None
        # Should only be called once since no simplification is possible
        assert mock_get.call_count <= 1


class TestAddressToCoordinates:
    """Test main address to coordinates conversion"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_nlsc_success(self, mock_get, geocoder, nlsc_response):
        """Test successful conversion using NLSC API"""
        mock_response = MagicMock()
        mock_response.json.return_value = nlsc_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert result is not None
        assert len(result) == 2
        lat, lng = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_nominatim_fallback(self, mock_get, geocoder, nominatim_response):
        """Test fallback to Nominatim when NLSC fails"""
        mock_response = MagicMock()
        # First call (NLSC) returns empty, second call (Nominatim) succeeds
        mock_response.json.side_effect = [[], nominatim_response]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert result is not None
        assert len(result) == 2
        assert mock_get.call_count == 2

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_simplified_fallback(self, mock_get, geocoder, nominatim_response):
        """Test fallback to simplified address when full address fails"""
        mock_response = MagicMock()
        # NLSC fails, first Nominatim fails, simplified Nominatim succeeds
        mock_response.json.side_effect = [[], [], nominatim_response]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert result is not None
        assert len(result) == 2

    @patch.object(Geocoder, "_query_tgos")
    @patch.object(Geocoder, "_try_simplified_addresses")
    @patch.object(Geocoder, "_query_nominatim")
    @patch.object(Geocoder, "_query_nlsc")
    def test_address_to_coordinates_tgos_fallback(self, mock_nlsc, mock_nominatim, mock_simplified, mock_tgos, geocoder):
        """Test fallback to TGOS when all other APIs fail"""
        # All APIs except TGOS return None
        mock_nlsc.return_value = None
        mock_nominatim.return_value = None
        mock_simplified.return_value = None
        mock_tgos.return_value = (25.018269, 121.471703)

        result = geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert result is not None
        assert len(result) == 2
        assert result == (25.018269, 121.471703)

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_all_fail(self, mock_get, geocoder):
        """Test GeocodingError when all APIs fail"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingError) as exc_info:
            geocoder.address_to_coordinates("Invalid Address")

        error_msg = str(exc_info.value)
        assert "無法找到地址的座標" in error_msg
        assert "Google Maps" in error_msg

    @patch.object(Geocoder, "_query_nlsc")
    def test_address_to_coordinates_request_exception(self, mock_nlsc, geocoder):
        """Test handling of request exceptions"""
        # Simulate RequestException raised during API call
        mock_nlsc.side_effect = requests.RequestException("Network error")

        with pytest.raises(GeocodingError) as exc_info:
            geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert "地址查詢失敗" in str(exc_info.value)

    @patch.object(Geocoder, "_query_nlsc")
    def test_address_to_coordinates_generic_exception(self, mock_nlsc, geocoder):
        """Test handling of generic exceptions"""
        # Simulate a generic exception raised during API call
        mock_nlsc.side_effect = ValueError("Unexpected error")

        with pytest.raises(GeocodingError) as exc_info:
            geocoder.address_to_coordinates("新北市板橋區民生路二段80號")

        assert "地址轉換錯誤" in str(exc_info.value)

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_custom_timeout(self, mock_get, geocoder, nlsc_response):
        """Test that custom timeout is passed to API calls"""
        mock_response = MagicMock()
        mock_response.json.return_value = nlsc_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        geocoder.address_to_coordinates("新北市板橋區民生路二段80號", timeout=30)

        # Verify timeout was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == 30

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_address_to_coordinates_cleans_address(self, mock_get, geocoder, nlsc_response):
        """Test that address is cleaned before geocoding"""
        mock_response = MagicMock()
        mock_response.json.return_value = nlsc_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Address with spaces
        geocoder.address_to_coordinates("板橋區 民生路 二段 80號")

        # Verify cleaned address was used (no spaces, with default city)
        call_kwargs = mock_get.call_args[1]
        assert "params" in call_kwargs
        called_address = call_kwargs["params"]["addr"]
        assert " " not in called_address
        assert called_address.startswith("新北市")


class TestGetCurrentLocationFromAddress:
    """Test convenience function"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_get_current_location_from_address_success(self, mock_get, nlsc_response):
        """Test convenience function with successful geocoding"""
        mock_response = MagicMock()
        mock_response.json.return_value = nlsc_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_current_location_from_address("新北市板橋區民生路二段80號")

        assert result is not None
        assert len(result) == 2
        lat, lng = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_get_current_location_from_address_failure(self, mock_get):
        """Test convenience function with geocoding failure"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingError):
            get_current_location_from_address("Invalid Address")


class TestTimeoutHandling:
    """Test timeout handling across all API methods"""

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_timeout_in_nlsc(self, mock_get, geocoder):
        """Test timeout handling in NLSC API"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_nlsc("新北市板橋區民生路二段80號", timeout=5)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_timeout_in_nominatim(self, mock_get, geocoder):
        """Test timeout handling in Nominatim API"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_nominatim("新北市板橋區民生路二段80號", timeout=5)

        assert result is None

    @patch("trash_tracking_core.utils.geocoding.requests.get")
    def test_timeout_in_tgos(self, mock_get, geocoder):
        """Test timeout handling in TGOS API"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = geocoder._query_tgos("新北市板橋區民生路二段80號", timeout=5)

        assert result is None

    @patch.object(Geocoder, "_query_nlsc")
    def test_timeout_propagates_to_geocoding_error(self, mock_nlsc, geocoder):
        """Test that timeout in all APIs results in GeocodingError"""
        # Simulate timeout exception raised during API call
        mock_nlsc.side_effect = requests.Timeout("Connection timeout")

        with pytest.raises(GeocodingError) as exc_info:
            geocoder.address_to_coordinates("新北市板橋區民生路二段80號", timeout=5)

        assert "地址查詢失敗" in str(exc_info.value)
