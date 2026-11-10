# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Metrics tracking for OGR API calls.

This module provides a lightweight metrics tracking system to count
API calls per instance URL and namespace. Metrics are stored in-memory
and are NOT thread-safe or process-synchronized.

The track_ogr_request decorator can be applied to GitProject methods
to automatically track API calls. The instance URL uniquely identifies
the service instance (e.g., github.com, gitlab.com, gitlab.example.com).
"""

from __future__ import annotations

import functools
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

if TYPE_CHECKING:
    from ogr.abstract import GitProject

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


class RequestMetricsTracker:
    """
    Tracker for counting API calls per instance URL and namespace.

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
        instance_url: str,
        namespace: str,
    ) -> None:
        """
        Record an API request for a given instance URL and namespace.

        Args:
            instance_url: The service instance URL (e.g., "https://github.com", "https://gitlab.com")
            namespace: The namespace (e.g., "packit", "rpms")
        """
        key = (instance_url, namespace)
        self._counts[key] += 1

    def get_all_counts(self) -> dict[tuple[str, str], int]:
        """
        Get all request counts.

        Returns:
            Dictionary mapping (instance_url, namespace) tuples to counts.
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


def record_ogr_request(instance_url: str, namespace: str) -> None:
    """
    Record an ogr API request.

    This is a convenience function that uses the global metrics tracker.

    Args:
        instance_url: The service instance URL (e.g., "https://github.com", "https://gitlab.com")
        namespace: The namespace (e.g., "packit-service", "rpms")
    """
    _metrics_tracker.record_request(instance_url, namespace)


def track_ogr_request(func: F) -> F:
    """
    Decorator to track ogr API method calls.

    The decorated method must be called on a GitProject instance
    (which has `namespace`, `repo`, and `service` attributes).

    For Pagure projects, the namespace is combined with the repo name
    (e.g., "rpms/python-requests") to provide more granular metrics.

    The instance URL is extracted from the service to distinguish between
    different instances (e.g., multiple GitLab or Forgejo instances).

    Example:
        @track_ogr_request
        def get_issues(self):
            ...
    """

    @functools.wraps(func)
    def wrapper(self: GitProject, *args: Any, **kwargs: Any) -> Any:
        try:
            from ogr.services.pagure import PagureService

            namespace = self.namespace
            instance_url = self.service.instance_url

            # For Pagure, append the repo name to the namespace
            # to get more granular metrics (e.g., "rpms/python-requests")
            if isinstance(self.service, PagureService) and self.repo:
                namespace = f"{namespace}/{self.repo}"

            record_ogr_request(instance_url, namespace)
        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")

        return func(self, *args, **kwargs)

    return cast(F, wrapper)


__all__ = [
    "RequestMetricsTracker",
    "get_metrics_tracker",
    "record_ogr_request",
    "track_ogr_request",
]
