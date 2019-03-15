import datetime

import pytest

from ogr.abstract import PRComment
from ogr.utils import filter_comments, search_in_comments


@pytest.fixture()
def comments():
    return [
        PRComment(
            comment="Abc def ghi.",
            author="Mr. Smith",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            comment="something 12345 different",
            author="Mr. Bean",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            comment="Just a comment.",
            author="Mr. Doe",
            created=datetime.datetime(2019, 1, 18, 10, 14, 5),
            edited=datetime.datetime(2019, 1, 18, 10, 18, 5),
        ),
        PRComment(
            comment="Just some notes.",
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
    "filter_str,number_of_result",
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
    "filter_str,starts_with,number_of_groups",
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
