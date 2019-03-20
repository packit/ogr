# mocking github interface
import inspect
import os
import github


def logcall(name, args, kwargs):
    output = "Github API call: {}".format(name)
    output += ("(")
    if args or kwargs:

        if len(args)==1:
            output += str(args)[1:-2]
        elif len(args)>1:
            output += str(args)[1:-1]
        if kwargs:
            if args:
                output += ", "
            output += "**{}".format(kwargs)
    output += (")")
    print(output)
    #print([x[3] for x in inspect.stack()])
    return output


class MockClass(object):
    mock_class = None

    def __init__(self, *args, **kwargs):
        logcall("__init__", args, kwargs)

    def __getattr__(self, name):
        def method(*args, **kwargs):
            if self.mock_class is not None:
                if not any([name in foo for foo in inspect.getmembers(self.mock_class, predicate=inspect.isfunction)]):
                    raise NotImplementedError("function:{} is not supported by {} class".format(name, self.mock_class))
            logcall(name, args, kwargs)
            return MockClass()
        return method

class MockProject(MockClass):
    mock_class = github.Project.Project

    def get_pr_comments(self, *args, **kwargs):
        logcall("get_pr_comments", args, kwargs)
        return []

class MockGithub(MockClass):
    mock_class = github.Github

    def get_project(self, *args, **kwargs):
        logcall("get_project", args, kwargs)
        return MockProject


def test_full_mocking():
    a = MockGithub()
    a.get_repo("a", 1, kwarg="value")
    a.get_repo().xxx()
    a.xxx()

#test_full_mocking()