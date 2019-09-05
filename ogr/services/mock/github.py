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

import requests
from github import (
    Consts,
    Installation,
    InstallationAuthorization,
    GithubException,
    BadCredentialsException,
    UnknownObjectException,
)
from github.MainClass import DEFAULT_BASE_URL

from ogr.persistent_storage import use_persistent_storage_without_overwriting
from ogr.services.github_tweak import BetterGithubIntegration


class BetterGithubIntegrationMockResponse:
    def __init__(self, json, status_code=None) -> None:
        self._json = json
        self.status_code = status_code

    def json(self):
        return self._json


@use_persistent_storage_without_overwriting
class BetterGithubIntegrationMock(BetterGithubIntegration):
    def get_installation(self, owner, repo):
        """
        :calls: `GET /repos/:owner/:repo/installation
                <https://developer.github.com/v3/apps/#get-a-repository-installation>`_
        :param owner: str
        :param repo: str
        :rtype: :class:`github.Installation.Installation`
        """
        headers = {
            "Authorization": "Bearer {}".format(self.create_jwt()),
            "Accept": Consts.mediaTypeIntegrationPreview,
            "User-Agent": "PyGithub/Python",
        }

        response = self.get_raw_request(
            "{}/repos/{}/{}/installation".format(DEFAULT_BASE_URL, owner, repo),
            headers=headers,
        )
        response_dict = response.json()
        return Installation.Installation(None, headers, response_dict, True)

    def get_raw_request(self, url, headers=None):
        keys_internal = [url]
        if self.persistent_storage.is_write_mode:
            output = requests.get(url, headers=headers)
            self.persistent_storage.store(keys=keys_internal, values=output.json())
        else:
            output_dict = self.persistent_storage.read(keys=keys_internal)
            output = BetterGithubIntegrationMockResponse(json=output_dict)
        return output

    def post_raw_request(self, url, headers=None, json=None):
        keys_internal = [url]
        if self.persistent_storage.is_write_mode:
            output = requests.post(url, headers=headers, json=json)
            self.persistent_storage.store(
                keys=keys_internal,
                values={"json": output.json(), "status_code": output.status_code},
            )
        else:
            output_dict = self.persistent_storage.read(keys=keys_internal)
            output = BetterGithubIntegrationMockResponse(
                json=output_dict["json"], status_code=output_dict["status_code"]
            )
        return output

    def get_access_token(self, installation_id, user_id=None):
        """
        Get an access token for the given installation id.
        POSTs https://api.github.com/app/installations/<installation_id>/access_tokens
        :param user_id: int
        :param installation_id: int
        :return: :class:`github.InstallationAuthorization.InstallationAuthorization`
        """
        body = {}
        if user_id:
            body = {"user_id": user_id}
        response = self.post_raw_request(
            url="https://api.github.com/app/installations/{}/access_tokens".format(
                installation_id
            ),
            headers={
                "Authorization": "Bearer {}".format(self.create_jwt()),
                "Accept": Consts.mediaTypeIntegrationPreview,
                "User-Agent": "PyGithub/Python",
            },
            json=body,
        )

        if response.status_code == 201:
            return InstallationAuthorization.InstallationAuthorization(
                requester=None,  # not required, this is a NonCompletableGithubObject
                headers={},  # not required, this is a NonCompletableGithubObject
                attributes=response.json(),
                completed=True,
            )
        elif response.status_code == 403:
            raise BadCredentialsException(
                status=response.status_code, data=response.text
            )
        elif response.status_code == 404:
            raise UnknownObjectException(
                status=response.status_code, data=response.text
            )
        raise GithubException(status=response.status_code, data=response.text)
