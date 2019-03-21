import pytest
from ogr.services.mock.github_mock import MockGithub

def test_full_mocking():
    a = MockGithub()
    a.get_repo("a", 1, kwarg="value")
    a.get_repo().xxx()
    try:
        a.xxx()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("this has to raise error because method is not in class")
    assert a.get_project(1, 1).url() == "https://lol.wat"
    assert a.get_project(1, 1).get_columns().mock_return("https://lol.wat") == "https://lol.wat"
