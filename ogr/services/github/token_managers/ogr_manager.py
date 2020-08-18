# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT


import github


from ogr.abstract import GithubTokenManager
from ogr.exceptions import OgrException
from ogr.services import github as ogr_github


class OgrGithubTokenManager(GithubTokenManager):
    def __init__(self, service: "ogr_github.GithubService"):
        self.service = service
        self.integration = github.GithubIntegration(
            service.github_app_id, service.github_app_private_key
        )

    def get_pygithub_instance(self, namespace: str, repo: str) -> github.Github:
        inst_id = self.integration.get_installation(namespace, repo).id
        # PyGithub<1.52 returned an object for id, with a value attribute,
        # which was None or an ID.
        # This was changed in:
        # https://github.com/PyGithub/PyGithub/commit/61808da15e8e3bcb660acd0e7947326a4a6c0c7a#diff-b8f1ee87df332916352809a397ea259aL54
        # 'id' is now None or an ID.
        inst_id = (
            inst_id if isinstance(inst_id, int) or inst_id is None else inst_id.value
        )
        if not inst_id:
            raise OgrException(
                f"No installation ID provided for {namespace}/{repo}: "
                "please make sure that you provided correct credentials of your GitHub app."
            )
        inst_auth = self.integration.get_access_token(inst_id)
        return github.Github(login_or_token=inst_auth.token)
