import logging

import github
import requests

from ogr.exceptions import GithubAPIException
from ogr.utils import RequestResponse

logger = logging.getLogger(__name__)


# TODO: upstream this to PyGithub
class BetterGithubIntegration(github.GithubIntegration):
    """
    A "fork" of GithubIntegration class from PyGithub.

    Since we auth as a Github app, we need to get an installation ID
    of the app within a repo. Then we are able to get the API token
    and work with Github's REST API
    """

    def __init__(self, integration_id, private_key):
        super().__init__(integration_id, private_key)
        self.session = requests.session()

        adapter = requests.adapters.HTTPAdapter(max_retries=5)
        self.session.mount("https://", adapter)

    def get_raw_request(
        self, url, method="GET", params=None, data=None, header=None
    ) -> RequestResponse:

        response = self.session.request(
            method=method, url=url, params=params, headers=header, data=data
        )

        json_output = None
        try:
            json_output = response.json()
        except ValueError:
            logger.debug(response.text)

        return RequestResponse(
            status_code=response.status_code,
            ok=response.ok,
            content=response.content,
            json=json_output,
            reason=response.reason,
        )

    def get_installation_id_for_repo(self, namespace: str, repo: str) -> int:
        """
        Get repo installation ID for a repository
        """

        response = self.get_raw_request(
            method="GET",
            url=f"https://api.github.com/repos/{namespace}/{repo}/installation",
            header={
                "Authorization": "Bearer {}".format(self.create_jwt()),
                "Accept": "application/vnd.github.machine-man-preview+json",
                "User-Agent": "PyGithub/Python",
            },
            data=None,
        )

        if response.status_code != 200:
            logger.debug(response.content)
            raise GithubAPIException(
                f"Unable to obtain installation ID for repo {namespace}/{repo}."
            )
        try:
            return response.json["id"]
        except KeyError:
            raise GithubAPIException(
                f"This Github app is not installed in {namespace}/{repo}."
            )
