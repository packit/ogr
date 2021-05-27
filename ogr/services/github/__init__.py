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

from ogr.services.github.release import GithubRelease
from ogr.services.github.user import GithubUser
from ogr.services.github.project import GithubProject
from ogr.services.github.service import GithubService
from ogr.services.github.comments import GithubIssueComment, GithubPRComment
from ogr.services.github.issue import GithubIssue
from ogr.services.github.pull_request import GithubPullRequest
from ogr.services.github.check_run import GithubCheckRun

__all__ = [
    GithubCheckRun.__name__,
    GithubPullRequest.__name__,
    GithubIssueComment.__name__,
    GithubPRComment.__name__,
    GithubIssue.__name__,
    GithubRelease.__name__,
    GithubUser.__name__,
    GithubProject.__name__,
    GithubService.__name__,
]
