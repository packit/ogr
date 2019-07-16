import requests
from github import Consts, Installation
from github.MainClass import DEFAULT_BASE_URL

from ogr import use_persistent_storage_without_overwriting
from ogr.services.github_tweak import BetterGithubIntegration


class BetterGithubIntegrationMockResponse:
    def __init__(self, json) -> None:
        self._json = json

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
            output = requests.get(url, header=headers)
            self.persistent_storage.store(keys=keys_internal, values=output.json())
        else:
            output_dict = self.persistent_storage.read(keys=keys_internal)
            output = BetterGithubIntegrationMockResponse(json=output_dict)
        return output
