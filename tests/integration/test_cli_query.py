"""
Integration Test Suite 1: CLI Query Functionality

Tests the CLI's ability to query garbage truck information
from real NTPC API endpoints.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_PATH = PROJECT_ROOT / "cli.py"


class TestCLIQuery:
    """Test Suite 1: CLI 查詢功能"""

    def test_query_by_address(self):
        """Test querying garbage trucks by address"""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "--address", "新北市板橋區中山路一段161號"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"CLI failed with error: {result.stderr}"
        assert "Found" in result.stdout or "找到" in result.stdout
        assert "Route" in result.stdout or "路線" in result.stdout

    def test_query_with_custom_radius(self):
        """Test querying with custom search radius"""
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "--address",
                "新北市板橋區中山路一段161號",
                "--radius",
                "2000",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "Found" in result.stdout or "找到" in result.stdout

    def test_query_with_line_filter(self):
        """Test filtering by specific route line"""
        # First get all routes to find a valid line name
        result_all = subprocess.run(
            [sys.executable, str(CLI_PATH), "--address", "新北市板橋區中山路一段161號"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result_all.returncode == 0:
            # Try to extract a line name from output
            lines = result_all.stdout.split("\n")
            for line in lines:
                if "Route:" in line or "路線:" in line:
                    # Extract route name
                    route_name = line.split(":")[-1].strip()
                    if route_name:
                        # Now test with this specific route
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(CLI_PATH),
                                "--address",
                                "新北市板橋區中山路一段161號",
                                "--line",
                                route_name,
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        assert result.returncode == 0
                        assert route_name in result.stdout
                        break

    def test_query_with_custom_next_points(self):
        """Test querying with custom number of next points"""
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "--address",
                "新北市板橋區中山路一段161號",
                "--next",
                "5",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "Found" in result.stdout or "找到" in result.stdout

    def test_invalid_address_handling(self):
        """Test error handling for invalid address"""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "--address", "InvalidAddress123456"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should either fail gracefully or show an error message
        assert "error" in result.stderr.lower() or result.returncode != 0 or "找不到" in result.stdout

    def test_no_address_error(self):
        """Test error handling when no address is provided"""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should show error message about missing address
        assert result.returncode == 1
        assert "錯誤" in result.stderr or "請提供地址" in result.stderr or "--address" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
