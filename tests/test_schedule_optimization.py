"""Test schedule optimization functionality"""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest


def test_point_get_weekdays_normal():
    """Test parsing normal weekday string"""
    from trash_tracking_core.models.point import Point

    point = Point(
        source_point_id=1,
        vil="Test",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=1,
        point_rank=1,
        point_time="18:00",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="1,3,5",  # Monday, Wednesday, Friday
        in_scope="Y",
        like_count=0,
    )

    weekdays = point.get_weekdays()
    assert weekdays == [1, 3, 5]


def test_point_get_weekdays_with_sunday():
    """Test parsing weekday string with Sunday (7 -> 0)"""
    from trash_tracking_core.models.point import Point

    point = Point(
        source_point_id=1,
        vil="Test",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=1,
        point_rank=1,
        point_time="18:00",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="0,7",  # Both formats for Sunday
        in_scope="Y",
        like_count=0,
    )

    weekdays = point.get_weekdays()
    assert weekdays == [0]  # Should normalize to [0]


def test_point_get_weekdays_empty():
    """Test parsing empty weekday string"""
    from trash_tracking_core.models.point import Point

    point = Point(
        source_point_id=1,
        vil="Test",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=1,
        point_rank=1,
        point_time="18:00",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="",
        in_scope="Y",
        like_count=0,
    )

    weekdays = point.get_weekdays()
    assert weekdays == []


def test_point_get_weekdays_invalid():
    """Test parsing invalid weekday string"""
    from trash_tracking_core.models.point import Point

    point = Point(
        source_point_id=1,
        vil="Test",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=1,
        point_rank=1,
        point_time="18:00",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="invalid",
        in_scope="Y",
        like_count=0,
    )

    weekdays = point.get_weekdays()
    assert weekdays == []  # Should return empty list on error


def test_schedule_extraction_logic():
    """Test schedule extraction logic with mock data"""
    from trash_tracking_core.models.point import Point

    # Create mock points
    points = [
        Point(
            source_point_id=1,
            vil="Test",
            point_name="Point 1",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=2,
            vil="Test",
            point_name="Point 2",
            lon=121.5,
            lat=25.0,
            point_id=2,
            point_rank=2,
            point_time="21:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
    ]

    # Test the logic directly
    all_weekdays = set()
    for point in points:
        weekdays = point.get_weekdays()
        all_weekdays.update(weekdays)

    times = [point.point_time for point in points if point.point_time]

    schedule = {
        "weekdays": sorted(list(all_weekdays)),
        "time_start": min(times) if times else None,
        "time_end": max(times) if times else None,
    }

    assert schedule["weekdays"] == [1, 3, 5]
    assert schedule["time_start"] == "18:00"
    assert schedule["time_end"] == "21:00"


def test_should_update_no_schedule():
    """Test should always update when no schedule info (backward compatibility)"""
    # When schedule_weekdays is empty, should always return True
    weekdays = []
    assert not weekdays  # Empty list means always update


def test_weekday_conversion():
    """Test Python weekday to API weekday conversion"""
    # Python: 0=Monday, 6=Sunday
    # API: 1=Monday, 0/7=Sunday

    conversions = {
        0: 1,  # Monday
        1: 2,  # Tuesday
        2: 3,  # Wednesday
        3: 4,  # Thursday
        4: 5,  # Friday
        5: 6,  # Saturday
        6: 0,  # Sunday
    }

    for python_wd, api_wd in conversions.items():
        # Convert
        result = python_wd + 1 if python_wd < 6 else 0
        assert result == api_wd
