import logging

import github
import requests
from github import Consts, Installation
from github.MainClass import DEFAULT_BASE_URL

logger = logging.getLogger(__name__)


class BetterGithubIntegration(github.GithubIntegration):
    """
    A "fork" of GithubIntegration class from PyGithub.

    Since we auth as a Github app, we need to get an installation ID
    of the app within a repo. Then we are able to get the API token
    and work with Github's REST API

    The code should be same as the master version of PyGithub.
    (Leave it here for backwards compatibility.)
    """

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

        response = requests.get(
            "{}/repos/{}/{}/installation".format(DEFAULT_BASE_URL, owner, repo),
            headers=headers,
        )
        response_dict = response.json()
        return Installation.Installation(None, headers, response_dict, True)
