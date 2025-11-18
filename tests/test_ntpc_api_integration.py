"""New Taipei City API integration tests"""

import pytest
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.models.truck import TruckLine


class TestNTPCApiIntegration:
    """NTPC API integration tests"""

    @pytest.fixture
    def client(self):
        return NTPCApiClient()

    def test_get_around_points_success(self, client):
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        assert isinstance(result, list), "Result should be a list"

        if len(result) > 0:
            truck = result[0]

            assert isinstance(truck, TruckLine), "Result should be TruckLine object"

            assert truck.line_id, "line_id should not be empty"
            assert truck.line_name, "line_name should not be empty"
            assert truck.car_no, "car_no should not be empty"
            assert truck.area, "area should not be empty"

            assert isinstance(truck.arrival_rank, int), "arrival_rank should be integer"
            assert isinstance(truck.diff, int), "diff should be integer"
            assert truck.arrival_rank >= 0, "arrival_rank should be non-negative"
            assert len(truck.points) > 0, "Should have collection point data"

            assert 24.0 < truck.location_lat < 26.0, "Latitude should be within reasonable range"
            assert 121.0 < truck.location_lon < 122.0, "Longitude should be within reasonable range"

            print(f"\nFound {len(result)} trash trucks")
            print(f"First: {truck.line_name} ({truck.car_no})")
            print(f"Current location: {truck.location}")
            print(f"Stop: {truck.arrival_rank}/{len(truck.points)}")
            print(f"Delay status: {truck.diff} minutes")

    def test_get_around_points_data_consistency(self, client):
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            for truck in result:
                assert truck.arrival_rank <= len(truck.points), \
                    f"{truck.line_name}: arrival_rank should not exceed total points"

                point_ranks = [p.point_rank for p in truck.points]
                assert len(point_ranks) == len(set(point_ranks)), \
                    f"{truck.line_name}: point_rank should be unique"

                current_point = truck.get_current_point()
                if truck.arrival_rank > 0:
                    assert current_point is not None, \
                        f"{truck.line_name}: Should have current collection point"

    def test_get_around_points_upcoming_logic(self, client):
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            for truck in result:
                upcoming = truck.get_upcoming_points()

                for point in upcoming:
                    assert point.point_rank > truck.arrival_rank, \
                        f"{truck.line_name}: Upcoming point rank should be greater than current rank"

                ranks = [p.point_rank for p in upcoming]
                assert ranks == sorted(ranks), \
                    f"{truck.line_name}: Upcoming points should be sorted by rank"

                print(f"\n{truck.line_name}:")
                print(f"  Current stop number: {truck.arrival_rank}")
                print(f"  Remaining points: {len(upcoming)}")
                if upcoming:
                    print(f"  Next point: {upcoming[0].point_name} (rank: {upcoming[0].point_rank})")

    def test_get_around_points_point_status(self, client):
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            truck = result[0]

            passed_points = [p for p in truck.points if p.has_passed()]
            for point in passed_points:
                assert point.arrival is not None, "Passed points should have arrival time"

            upcoming = truck.get_upcoming_points()
            for point in upcoming:
                assert not point.arrival or point.arrival == "", \
                    "Upcoming points should not have arrival time"

            print(f"\n{truck.line_name} collection point status:")
            print(f"  Passed: {len(passed_points)} points")
            print(f"  Upcoming: {len(upcoming)} points")

    def test_get_around_points_invalid_coordinates(self, client):
        lat, lng = 25.0, 120.0

        result = client.get_around_points(lat, lng)

        assert isinstance(result, list), "Should return list even with no results"

    def test_api_retry_mechanism(self):
        client = NTPCApiClient(
            base_url="https://invalid-url-for-testing.example.com",
            retry_count=2,
            retry_delay=1
        )

        with pytest.raises(NTPCApiError) as exc_info:
            client.get_around_points(25.0199, 121.4705)

        assert "重試" in str(exc_info.value)
        print(f"\nRetry mechanism working: {exc_info.value}")

    def test_concurrent_requests(self, client):
        import concurrent.futures

        lat, lng = 25.0199, 121.4705

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(client.get_around_points, lat, lng)
                for _ in range(3)
            ]

            results = [future.result() for future in futures]

        for result in results:
            assert isinstance(result, list), "Each request should return a list"

        print(f"\nConcurrent request test passed, {len(results)} requests")

    def test_response_time(self, client):
        import time

        lat, lng = 25.0199, 121.4705

        start_time = time.time()
        result = client.get_around_points(lat, lng)
        elapsed_time = time.time() - start_time

        assert elapsed_time < 10, f"Response time too long: {elapsed_time:.2f} seconds"

        print(f"\nAPI response time: {elapsed_time:.2f} seconds")
        print(f"   Found {len(result)} trucks")
