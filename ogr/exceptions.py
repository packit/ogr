# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class OgrException(Exception):
    """ Something went wrong during our execution """


class PagureAPIException(OgrException):
    """ Exception related to Pagure API """

    def __init__(self, *args: object, pagure_error: str = None) -> None:
        super().__init__(*args)
        self.pagure_error = pagure_error


class GithubAPIException(OgrException):
    """ Exception related to Github API """

    def __init__(self, *args: object, github_error: str = None) -> None:
        super().__init__(*args)
        self.github_error = github_error


class PersistenStorageException(OgrException):
    """ Mocking Exceptions for persistent storage of objects """


class OurPagureRawRequest(OgrException):
    """ Mocking Exceptions for pagure raw request """


class OperationNotSupported(OgrException):
    """ Raise when the operation is not supported by the backend. """
