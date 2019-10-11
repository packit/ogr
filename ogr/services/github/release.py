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

from github.GitRelease import GitRelease as PyGithubRelease

from ogr.abstract import Release, GitTag
from ogr.services import github as ogr_github


class GithubRelease(Release):
    project: "ogr_github.GithubProject"

    def __init__(
        self,
        tag_name: str,
        url: str,
        created_at: str,
        tarball_url: str,
        git_tag: GitTag,
        project: "ogr_github.GithubProject",
        raw_release: PyGithubRelease,
    ) -> None:
        super().__init__(tag_name, url, created_at, tarball_url, git_tag, project)
        self.raw_release = raw_release

    @property
    def title(self):
        return self.raw_release.title

    @property
    def body(self):
        return self.raw_release.body

    def edit_release(self, name: str, message: str) -> None:
        """
        Edit name and message of a release.

        :param name: str
        :param message: str
        """
        self.raw_release = self.raw_release.update_release(name=name, message=message)
