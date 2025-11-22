"""Mock data for NTPC API responses in BDD tests"""

from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine

# Mock truck line data for testing
MOCK_TRUCK_POINTS = [
    Point(
        source_point_id=1001,
        vil="板橋區",
        point_name="Minsheng Rd. Sec. 2, No. 120",
        lon=121.4690,
        lat=25.0170,
        point_id=1,
        point_rank=1,
        point_time="18:00",
        arrival="17:58",
        arrival_diff=2,
        fixed_point=1,
        point_weekknd="N",
        in_scope="Y",
        like_count=10,
    ),
    Point(
        source_point_id=1002,
        vil="板橋區",
        point_name="Minsheng Rd. Sec. 2, No. 80",
        lon=121.4717,
        lat=25.0183,
        point_id=2,
        point_rank=2,
        point_time="18:05",
        arrival="18:03",
        arrival_diff=2,
        fixed_point=1,
        point_weekknd="N",
        in_scope="Y",
        like_count=15,
    ),
    Point(
        source_point_id=1003,
        vil="板橋區",
        point_name="Chenggong Rd. No. 50",
        lon=121.4730,
        lat=25.0190,
        point_id=3,
        point_rank=3,
        point_time="18:10",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="N",
        in_scope="Y",
        like_count=8,
    ),
    Point(
        source_point_id=1004,
        vil="板橋區",
        point_name="Chenggong Rd. No. 23",
        lon=121.4745,
        lat=25.0195,
        point_id=4,
        point_rank=4,
        point_time="18:15",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="N",
        in_scope="Y",
        like_count=12,
    ),
    Point(
        source_point_id=1005,
        vil="板橋區",
        point_name="Zhongshan Rd. Sec. 1, No. 200",
        lon=121.4760,
        lat=25.0200,
        point_id=5,
        point_rank=5,
        point_time="18:20",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="N",
        in_scope="Y",
        like_count=20,
    ),
]


def create_mock_truck_line(
    line_name: str = "A14路線下午",
    car_no: str = "KKA-0001",
    area: str = "板橋區",
    arrival_rank: int = 2,
    diff: int = 0,
) -> TruckLine:
    """
    Create a mock TruckLine for testing

    Args:
        line_name: Route name
        car_no: Vehicle number
        area: District name
        arrival_rank: Current position in route (1-based)
        diff: Estimated arrival time difference

    Returns:
        TruckLine: Mock truck line instance
    """
    current_point = MOCK_TRUCK_POINTS[arrival_rank - 1]
    truck = TruckLine(
        line_id="TEST001",
        line_name=line_name,
        area=area,
        arrival_rank=arrival_rank,
        diff=diff,
        car_no=car_no,
        location=current_point.point_name,
        location_lat=current_point.lat,
        location_lon=current_point.lon,
        bar_code="TEST_BARCODE",
        points=MOCK_TRUCK_POINTS,
    )
    return truck


def create_mock_truck_lines(count: int = 3) -> list[TruckLine]:
    """
    Create multiple mock truck lines for testing

    Args:
        count: Number of truck lines to create

    Returns:
        list[TruckLine]: List of mock truck lines
    """
    trucks = []
    routes = [
        ("A14路線下午", "KKA-0001", "板橋區", 2),
        ("B23路線上午", "KKA-0002", "板橋區", 3),
        ("C01路線下午", "KKA-0003", "板橋區", 1),
    ]

    for i in range(min(count, len(routes))):
        line_name, car_no, area, rank = routes[i]
        trucks.append(create_mock_truck_line(line_name, car_no, area, rank))

    return trucks


# Mock coordinates for test addresses
MOCK_ADDRESSES = {
    "新北市板橋區中山路一段161號": (25.0140, 121.4700),
    "新北市中和區中和路100號": (24.9980, 121.4950),
    "新北市新店區北新路三段200號": (24.9670, 121.5410),
}
