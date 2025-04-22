import logging
from typing import Protocol

from app.models.profile import Profile


class AnalyticsServiceProtocol(Protocol):
    async def identify(self, profile: Profile) -> None: ...
    def track(self, event: str, properties: dict) -> None: ...


class MockAnalyticsService(AnalyticsServiceProtocol):
    async def identify(self, profile: Profile) -> None:
        logger = logging.getLogger(__name__)
        logger.info(f"Mock identify called with profile: {profile}")

    def track(self, event: str, properties: dict) -> None:
        logger = logging.getLogger(__name__)
        logger.info(f"Mock track called with event: {event}, properties: {properties}")


def get_analytics_service() -> AnalyticsServiceProtocol:
    # In a real-world scenario, you would return an instance of the actual analytics service
    # For example, if you're using Segment:
    # return SegmentAnalyticsService()
    return MockAnalyticsService()


__all__ = ["AnalyticsServiceProtocol", "get_analytics_service"]
