"""Use Case Exceptions"""


class UseCaseError(Exception):
    """Base exception for use case errors"""

    pass


class NoRoutesFoundError(UseCaseError):
    """No routes found near the location"""

    pass


class RouteAnalysisError(UseCaseError):
    """Failed to analyze routes"""

    pass
