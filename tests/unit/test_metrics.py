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


class TestRequestMetricsTracker:
    """Tests for RequestMetricsTracker class."""

    def test_record_request_basic(self):
        """Test basic request recording."""
        tracker = RequestMetricsTracker()
        tracker.record_request("github", "packit")

        counts = tracker.get_all_counts()
        assert counts == {("github", "packit"): 1}

    def test_record_request_multiple(self):
        """Test recording multiple requests."""
        tracker = RequestMetricsTracker()
        tracker.record_request("github", "packit")
        tracker.record_request("github", "packit")
        tracker.record_request("github", "rpms")
        tracker.record_request("gitlab", "packit")

        counts = tracker.get_all_counts()
        assert counts == {
            ("github", "packit"): 2,
            ("github", "rpms"): 1,
            ("gitlab", "packit"): 1,
        }

    def test_get_all_counts_empty(self):
        """Test getting counts from empty tracker."""
        tracker = RequestMetricsTracker()
        counts = tracker.get_all_counts()
        assert counts == {}

    def test_reset(self):
        """Test resetting counters."""
        tracker = RequestMetricsTracker()
        tracker.record_request("github", "packit")
        tracker.record_request("gitlab", "rpms")

        # Verify counts before reset
        assert len(tracker.get_all_counts()) == 2

        # Reset and verify
        tracker.reset()
        counts = tracker.get_all_counts()
        assert counts == {}

    @pytest.mark.parametrize(
        ("service_type", "namespace", "count"),
        [
            ("github", "packit", 1),
            ("gitlab", "rpms", 5),
            ("pagure", "fedora-infrastructure", 10),
            ("forgejo", "example-org", 3),
        ],
    )
    def test_record_request_various_services(
        self,
        service_type: str,
        namespace: str,
        count: int,
    ):
        """Test recording requests for various service types."""
        tracker = RequestMetricsTracker()
        for _ in range(count):
            tracker.record_request(service_type, namespace)

        counts = tracker.get_all_counts()
        assert counts == {(service_type, namespace): count}


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

        record_ogr_request("github", "packit")
        record_ogr_request("github", "packit")

        counts = tracker.get_all_counts()
        assert counts[("github", "packit")] == 2


class TestTrackOgrRequestDecorator:
    """Tests for track_ogr_request decorator."""

    def test_decorator_tracks_request(self):
        """Test that decorator tracks requests correctly."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_project = flexmock(namespace="packit")

        @track_ogr_request("github")
        def test_method(self):
            return "success"

        result = test_method(mock_project)

        assert result == "success"

        counts = tracker.get_all_counts()
        assert counts == {("github", "packit"): 1}

    def test_decorator_with_none_namespace(self):
        """Test decorator when namespace is None (should not track)."""
        tracker = get_metrics_tracker()
        tracker.reset()

        # Create a mock project without namespace
        mock_project = flexmock(namespace=None)

        @track_ogr_request("github")
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

        @track_ogr_request("github")
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

        @track_ogr_request("github")
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

        @track_ogr_request("github")
        def example_method(self):
            """Example docstring."""
            return "result"

        assert example_method.__name__ == "example_method"
        assert example_method.__doc__ == "Example docstring."

    def test_decorator_with_multiple_calls(self):
        """Test decorator with multiple calls to same method."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_project = flexmock(namespace="packit")

        @track_ogr_request("github")
        def test_method(self):
            return "success"

        # Call multiple times
        for _ in range(5):
            test_method(mock_project)

        counts = tracker.get_all_counts()
        assert counts == {("github", "packit"): 5}

    def test_decorator_with_different_service_types(self):
        """Test decorator with different service types."""
        tracker = get_metrics_tracker()
        tracker.reset()

        mock_project = flexmock(namespace="packit")

        @track_ogr_request("github")
        def github_method(self):
            return "github"

        @track_ogr_request("gitlab")
        def gitlab_method(self):
            return "gitlab"

        github_method(mock_project)
        github_method(mock_project)
        gitlab_method(mock_project)

        counts = tracker.get_all_counts()
        assert counts == {
            ("github", "packit"): 2,
            ("gitlab", "packit"): 1,
        }

    def test_integration_with_different_namespaces(self):
        """Integration test with multiple namespaces."""
        tracker = get_metrics_tracker()
        tracker.reset()

        @track_ogr_request("github")
        def get_issues(self):
            return []

        project1 = flexmock(namespace="packit")
        project2 = flexmock(namespace="rpms")

        get_issues(project1)
        get_issues(project1)
        get_issues(project2)

        counts = tracker.get_all_counts()
        assert counts == {
            ("github", "packit"): 2,
            ("github", "rpms"): 1,
        }
