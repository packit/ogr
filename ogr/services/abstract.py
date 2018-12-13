class GitService:
    def __init__(self):
        pass

    @classmethod
    def create_from_remote_url(cls, remote_url):
        """
        Create instance of service from provided remote_url.

        :param remote_url: str
        :return: GitService
        """
        raise NotImplementedError()

    def get_project(self, namespace=None, user=None, repo=None):
        """
        Get the GitProject instance

        :param namespace: str
        :param user: str
        :param repo: str
        :return: GitProject
        """
        raise NotImplementedError

    @property
    def user(self):
        """
        GitUser instance for used token.

        :return: GitUser
        """
        raise NotImplementedError


class GitProject:
    def get_branches(self):
        """
        List of project branches.

        :return: [str]
        """
        raise NotImplementedError()

    def get_description(self):
        """
        Project description.

        :return: str
        """
        raise NotImplementedError()

    def pr_create(self, title, body, target_branch, current_branch):
        """
        Create a new pull request.

        :param title: str
        :param body: str
        :param target_branch: str
        :param current_branch: str
        :return: id of the new pull-request
        """
        raise NotImplementedError()

    def get_pr_list(self, status="open"):
        """
        List of pull requests (dics)

        :return: [{str: str}]
        """
        raise NotImplementedError()

    def get_pr_info(self, pr_id):
        """
        Get pull request info

        :param pr_id: int
        :return: {
            "title": "???",
            "id": "???",
            "status": "???",
            "url": "???",
            "description": "???"
            "username": "???",
            "source_project": "???",
            "target_project": "???",
            "source_branch": "???",
            "target_branch": "???"
        }
        """
        raise NotImplementedError()

    def get_pr_comments(self, pr_id):
        """
        Get list of pull-request comments.

        :param pr_id: int
        :return: [{
            "comment": "???",
            "author":"???",
            "created": "???"
            "edited": "???"
        }]
        """
        raise NotImplementedError()

    def pr_comment(self, pr_id, body, commit=None, filename=None, row=None):
        """
        Add new commit to the pull request.

        :param pr_id: int
        :param body: str
        :param commit: str
        :param filename: str
        :param row: int
        :return: ???
        """
        raise NotImplementedError()

    def pr_close(self, pr_id):
        """
        Close the pull-request.

        :param pr_id: int
        :return:  ???
        """
        raise NotImplementedError()

    def pr_merge(self, pr_id):
        """
        Merge the pull request.

        :param pr_id: int
        :return: ???
        """
        raise NotImplementedError()

    @property
    def fork(self):
        """
        GitProject instance of the fork if the fork exists, else None

        :return: GitProject or None
        """
        raise NotImplementedError()

    @property
    def is_forked(self):
        """
        True, if the project is forked by the user.

        :return: Bool
        """
        raise NotImplementedError()

    def fork_create(self):
        """
        Create a fork of the project.

        :return: ???
        """
        raise NotImplementedError()


class GitUser:
    @property
    def username(self):
        raise NotImplementedError()
