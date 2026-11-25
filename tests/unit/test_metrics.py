# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging

import pytest
from flexmock import flexmock

import ogr.metrics
from ogr.metrics import (
    RequestMetricsTracker,
    get_metrics_tracker,
    record_ogr_request,
    track_ogr_request,
)
from ogr.services.pagure import PagureService


class TestRequestMetricsTracker:
    """Tests for RequestMetricsTracker class."""

    def test_record_request_basic(self):
        """Test basic request recording."""
        tracker = RequestMetricsTracker()
        tracker.record_request("https://github.com", "packit")

        counts = tracker.get_all_counts()
        assert counts == {("https://github.com", "packit"): 1}

    def test_record_request_multiple(self):
        """Test recording multiple requests."""
        tracker = RequestMetricsTracker()
        tracker.record_request("https://github.com", "packit")
        tracker.record_request("https://github.com", "packit")
        tracker.record_request("https://github.com", "rpms")
        tracker.record_request("https://gitlab.com", "packit")

        counts = tracker.get_all_counts()
        assert counts == {
            ("https://github.com", "packit"): 2,
            ("https://github.com", "rpms"): 1,
            ("https://gitlab.com", "packit"): 1,
        }

    def test_get_all_counts_empty(self):
        """Test getting counts from empty tracker."""
        tracker = RequestMetricsTracker()
        counts = tracker.get_all_counts()
        assert counts == {}

    def test_reset(self):
        """Test resetting counters."""
        tracker = RequestMetricsTracker()
        tracker.record_request("https://github.com", "packit")
        tracker.record_request("https://gitlab.com", "rpms")

        # Verify counts before reset
        assert len(tracker.get_all_counts()) == 2

        # Reset and verify
        tracker.reset()
        counts = tracker.get_all_counts()
        assert counts == {}

    @pytest.mark.parametrize(
        ("instance_url", "namespace", "count"),
        [
            ("https://github.com", "packit", 1),
            ("https://gitlab.com", "rpms", 5),
            ("https://pagure.io", "fedora-infrastructure", 10),
            ("https://codeberg.org", "example-org", 3),
        ],
    )
    def test_record_request_various_services(
        self,
        instance_url: str,
        namespace: str,
        count: int,
    ):
        """Test recording requests for various service types."""
        tracker = RequestMetricsTracker()
        for _ in range(count):
            tracker.record_request(instance_url, namespace)

        counts = tracker.get_all_counts()
        assert counts == {(instance_url, namespace): count}

    def test_multiple_instances_same_service_type(self):
        """Test that different instances of the same service type are tracked separately."""
        tracker = RequestMetricsTracker()
        tracker.record_request("https://gitlab.com", "packit")
        tracker.record_request("https://gitlab.example.com", "packit")
        tracker.record_request("https://gitlab.com", "packit")
        tracker.record_request("https://codeberg.org", "myorg")
        tracker.record_request("https://forgejo.example.com", "myorg")

        counts = tracker.get_all_counts()
        assert counts == {
            ("https://gitlab.com", "packit"): 2,
            ("https://gitlab.example.com", "packit"): 1,
            ("https://codeberg.org", "myorg"): 1,
            ("https://forgejo.example.com", "myorg"): 1,
        }


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_metrics_tracker(self):
        """Test getting the global metrics tracker."""
        tracker1 = get_metrics_tracker()
        tracker2 = get_metrics_tracker()

        assert tracker1 is tracker2
        assert isinstance(tracker1, RequestMetricsTracker)

    def test_record_ogr_request(self):
        """Test the record_ogr_request convenience function."""
        tracker = get_metrics_tracker()
        tracker.reset()

        record_ogr_request("https://github.com", "packit")
        record_ogr_request("https://github.com", "packit")

        counts = tracker.get_all_counts()
        assert counts[("https://github.com", "packit")] == 2


class TestTrackOgrRequestDecorator:
    """Tests for track_ogr_request decorator."""

    def test_decorator_tracks_request(self):
        """Test that decorator tracks requests correctly."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_service = flexmock(instance_url="https://github.com")
        mock_project = flexmock(namespace="packit", service=mock_service)

        @track_ogr_request
        def test_method(self):
            return "success"

        result = test_method(mock_project)

        assert result == "success"

        counts = tracker.get_all_counts()
        assert counts == {("https://github.com", "packit"): 1}

    def test_decorator_with_none_namespace(self):
        """Test decorator when namespace is None (should not track)."""
        tracker = get_metrics_tracker()
        tracker.reset()

        # Create a mock project without namespace
        mock_project = flexmock(namespace=None)

        @track_ogr_request
        def test_method(self):
            return "success"

        result = test_method(mock_project)

        assert result == "success"

        counts = tracker.get_all_counts()
        assert counts == {}

    def test_decorator_with_missing_namespace_attribute(self):
        """Test decorator when object has no namespace attribute (should not track)."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_obj = flexmock()  # No namespace attribute

        @track_ogr_request
        def test_method(self):
            return "success"

        result = test_method(mock_obj)

        assert result == "success"

        counts = tracker.get_all_counts()
        assert counts == {}

    def test_decorator_handles_exceptions_silently(self, caplog):
        """Test that decorator catches exceptions during metric recording."""

        mock_project = flexmock(namespace="test-namespace")

        flexmock(ogr.metrics).should_receive("record_ogr_request").and_raise(
            ValueError("Test exception"),
        )

        @track_ogr_request
        def test_method(self):
            return "success"

        with caplog.at_level(logging.DEBUG):
            result = test_method(mock_project)

        # Verify method still returns successfully
        assert result == "success"

        # Verify exception was logged
        assert any(
            "Failed to record metrics" in record.message for record in caplog.records
        )

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @track_ogr_request
        def example_method(self):
            """Example docstring."""
            return "result"

        assert example_method.__name__ == "example_method"
        assert example_method.__doc__ == "Example docstring."

    def test_decorator_with_multiple_calls(self):
        """Test decorator with multiple calls to same method."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_service = flexmock(instance_url="https://github.com")
        mock_project = flexmock(namespace="packit", service=mock_service)

        @track_ogr_request
        def test_method(self):
            return "success"

        # Call multiple times
        for _ in range(5):
            test_method(mock_project)

        counts = tracker.get_all_counts()
        assert counts == {("https://github.com", "packit"): 5}

    def test_decorator_with_different_service_types(self):
        """Test decorator with different service types."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_github_service = flexmock(instance_url="https://github.com")
        mock_gitlab_service = flexmock(instance_url="https://gitlab.com")
        mock_github_project = flexmock(namespace="packit", service=mock_github_service)
        mock_gitlab_project = flexmock(namespace="packit", service=mock_gitlab_service)

        @track_ogr_request
        def github_method(self):
            return "github"

        @track_ogr_request
        def gitlab_method(self):
            return "gitlab"

        github_method(mock_github_project)
        github_method(mock_github_project)
        gitlab_method(mock_gitlab_project)

        counts = tracker.get_all_counts()
        assert counts == {
            ("https://github.com", "packit"): 2,
            ("https://gitlab.com", "packit"): 1,
        }

    def test_integration_with_different_namespaces(self):
        """Integration test with multiple namespaces."""
        tracker = get_metrics_tracker()
        tracker.reset()

        @track_ogr_request
        def get_issues(self):
            return []

        mock_service = flexmock(instance_url="https://github.com")
        project1 = flexmock(namespace="packit", service=mock_service)
        project2 = flexmock(namespace="rpms", service=mock_service)

        get_issues(project1)
        get_issues(project1)
        get_issues(project2)

        counts = tracker.get_all_counts()
        assert counts == {
            ("https://github.com", "packit"): 2,
            ("https://github.com", "rpms"): 1,
        }

    def test_decorator_pagure_appends_repo_to_namespace(self):
        """Test that Pagure decorator appends repo name to namespace."""
        tracker = get_metrics_tracker()
        tracker.reset()

        # Create mock Pagure service - must be actual instance for isinstance() check
        mock_service = flexmock(PagureService(instance_url="https://pagure.io"))
        mock_project = flexmock(
            namespace="rpms",
            repo="python-requests",
            service=mock_service,
        )

        @track_ogr_request
        def test_method(self):
            return "success"

        result = test_method(mock_project)

        assert result == "success"

        counts = tracker.get_all_counts()
        assert counts == {("https://pagure.io", "rpms/python-requests"): 1}

    def test_decorator_pagure_without_repo(self):
        """Test Pagure decorator when repo is None or empty."""
        tracker = get_metrics_tracker()
        tracker.reset()

        # Create mock Pagure service - must be actual instance for isinstance() check
        mock_service = flexmock(PagureService(instance_url="https://pagure.io"))
        mock_project = flexmock(namespace="rpms", repo=None, service=mock_service)

        @track_ogr_request
        def test_method(self):
            return "success"

        result = test_method(mock_project)

        assert result == "success"

        # Should fall back to just namespace when repo is None/empty
        counts = tracker.get_all_counts()
        assert counts == {("https://pagure.io", "rpms"): 1}
