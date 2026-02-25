# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Metrics tracking for OGR API calls.

This module provides a lightweight metrics tracking system to count
API calls per service type and namespace. Metrics are stored in-memory
and are NOT thread-safe or process-synchronized.

The track_ogr_request decorator can be applied to GitProject methods
to automatically track API calls.
"""

import functools
import logging
from collections import defaultdict
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


class RequestMetricsTracker:
    """
    Tracker for counting API calls per namespace and service type.

    Note: This class is NOT thread-safe and does NOT synchronize across processes.
    In a multi-worker environment, each worker maintains its own metrics, and some
    request counts may be lost. This is acceptable for approximate metrics tracking.
    The aggregation of data from multiple workers can be done in grafana dashboard.
    """

    def __init__(self):
        """Initialize the metrics tracker."""
        self._counts: dict[tuple[str, str], int] = defaultdict(int)

    def record_request(
        self,
        service_type: str,
        namespace: str,
    ) -> None:
        """
        Record an API request for a given service type and namespace.

        Args:
            service_type: The service type (e.g., "github", "gitlab", "pagure")
            namespace: The namespace (e.g., "packit", "rpms")
        """
        key = (service_type, namespace)
        self._counts[key] += 1

    def get_all_counts(self) -> dict[tuple[str, str], int]:
        """
        Get all request counts.

        Returns:
            Dictionary mapping (service_type, namespace) tuples to counts.
        """
        return {key: count for key, count in self._counts.items() if count > 0}

    def reset(self) -> None:
        """
        Reset all counters to zero.

        This is typically called after metrics have been collected and pushed.
        """
        self._counts.clear()


# Global instance
_metrics_tracker = RequestMetricsTracker()


def get_metrics_tracker() -> RequestMetricsTracker:
    """Get the global metrics tracker instance."""
    return _metrics_tracker


def record_ogr_request(service_type: str, namespace: str) -> None:
    """
    Record an ogr API request.

    This is a convenience function that uses the global metrics tracker.

    Args:
        service_type: The service type (e.g., "github", "gitlab", "pagure")
        namespace: The namespace (e.g., "packit-service", "rpms")
    """
    _metrics_tracker.record_request(service_type, namespace)


def track_ogr_request(service_type: str) -> Callable[[F], F]:
    """
    Decorator to track ogr API method calls.

    The decorated method must be called on a GitProject instance
    (which has `namespace` and `service` attributes).

    Args:
        service_type: The service type (e.g., "github", "gitlab", "pagure")

    Example:
        @track_ogr_request("github")
        def get_issues(self):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            namespace = getattr(self, "namespace", None)
            if namespace:
                try:
                    record_ogr_request(service_type, namespace)
                except Exception as e:
                    logger.debug(f"Failed to record metrics: {e}")

            return func(self, *args, **kwargs)

        return wrapper  # type: ignore

    return decorator


__all__ = [
    "RequestMetricsTracker",
    "get_metrics_tracker",
    "record_ogr_request",
    "track_ogr_request",
]
