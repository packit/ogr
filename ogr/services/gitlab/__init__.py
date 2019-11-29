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

from ogr.services.gitlab.release import GitlabRelease
from ogr.services.gitlab.user import GitlabUser
from ogr.services.gitlab.project import GitlabProject
from ogr.services.gitlab.service import GitlabService
from ogr.services.gitlab.comments import GitlabIssueComment, GitlabPRComment
from ogr.services.gitlab.issue import GitlabIssue
from ogr.services.gitlab.pull_request import GitlabPullRequest

__all__ = [
    GitlabIssue.__name__,
    GitlabPullRequest.__name__,
    GitlabIssueComment.__name__,
    GitlabPRComment.__name__,
    GitlabRelease.__name__,
    GitlabUser.__name__,
    GitlabProject.__name__,
    GitlabService.__name__,
]
