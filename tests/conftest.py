"""Pytest configuration for integration tests"""


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
