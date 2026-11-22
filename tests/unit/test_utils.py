# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import time

import pytest
from urllib3 import HTTPResponse

from ogr.abstract import PRComment
from ogr.utils import CustomRetry, filter_comments, search_in_comments


@pytest.fixture
def comments():
    return [
        PRComment(
            body="Abc def ghi.",
            author="Mr. Smith",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            body="something 12345 different",
            author="Mr. Bean",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            body="Just a comment.",
            author="Mr. Doe",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            body="Just some notes.",
            author="Mr. Brown",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
    ]


def test_filter_comments_empty():
    comments = filter_comments(comments=[], filter_regex="abcd")
    assert len(comments) == 0

    comments = filter_comments(comments=[], filter_regex="")
    assert len(comments) == 0


@pytest.mark.parametrize(
    ("filter_str", "number_of_result"),
    [
        ("unknown", 0),
        ("def", 1),
        ("some", 2),
        (r"\d+", 1),
        ("[a-zA-Z]+ [a-zA-Z]+ [a-zA-Z]+", 3),
    ],
)
def test_filter_comments(comments, filter_str, number_of_result):
    filtered_comments = filter_comments(comments=comments, filter_regex=filter_str)
    assert len(filtered_comments) == number_of_result


@pytest.mark.parametrize(
    ("filter_str", "starts_with", "number_of_groups"),
    [
        ("unknown", None, 0),
        ("def", "Abc", 1),
        ("some", "something", 1),
        (r"(\d+)", "some", 2),
        ("([a-zA-Z]*) ([a-zA-Z]*) ([a-zA-Z]*)", "Abc", 4),
    ],
)
def test_search_in_comments(comments, filter_str, starts_with, number_of_groups):
    match = search_in_comments(comments=comments, filter_regex=filter_str)
    if not number_of_groups:
        assert not match
    else:
        assert len(match.regs) == number_of_groups
        assert match.string.startswith(starts_with)


@pytest.mark.parametrize(
    ("status", "remaining", "expect_wait"),
    [
        # quota used up: wait until X-RateLimit-Reset
        (403, "0", True),
        (429, "0", True),
        # GitHub sends X-RateLimit-Reset on every response, including a 403
        # for missing permissions; that one is not a rate limit
        (403, "4733", False),
        (429, "12", False),
        # no X-RateLimit-Remaining: keep using X-RateLimit-Reset
        (403, None, True),
        # other statuses never look at the header
        (503, "0", False),
    ],
)
def test_custom_retry_ratelimit_reset(status, remaining, expect_wait):
    headers = {"X-RateLimit-Reset": str(int(time.time()) + 600)}
    if remaining is not None:
        headers["X-RateLimit-Remaining"] = remaining
    response = HTTPResponse(status=status, headers=headers)

    wait = CustomRetry().get_ratelimit_reset(response)

    if expect_wait:
        assert 590 < wait <= 600
    else:
        assert wait is None
