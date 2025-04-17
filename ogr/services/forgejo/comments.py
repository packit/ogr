# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from typing import Any

from ogr.abstract import Comment, CommitComment, IssueComment, PRComment, Reaction


class ForgejoReaction(Reaction):
    _raw_reaction: dict

    def __init__(
        self,
        raw_reaction: dict,
        forgejo_client: Any,
        repository: str,
        issue_number: int,
    ) -> None:
        """
        Initializes a ForgejoReaction.

        Args:
            raw_reaction (dict): The raw reaction data from the API.
            forgejo_client (Any): The Forgejo client instance.
            repository (str): Repository identifier (e.g., "owner/repo").
            issue_number (int): The issue number associated with the comment.
        """
        self._raw_reaction = raw_reaction
        self._forgejo_client = forgejo_client
        self._repository = repository
        self._issue_number = issue_number
        self._id = raw_reaction.get("id")
        self._content = raw_reaction.get("content")
        self._user_login = raw_reaction.get("user", {}).get("login")

    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

    def delete(self) -> None:
        """
        Deletes the reaction from Forgejo using the stored client context.
        """
        url = (
            f"{self._forgejo_client.forgejo_url}/api/v1/repos/"
            f"{self._repository}/issues/{self._issue_number}/reactions/{self._id}"
        )
        self._forgejo_client._make_request("DELETE", url)

    @property
    def content(self) -> str:
        return self._content

    @property
    def user_login(self) -> str:
        return self._user_login

    @property
    def id(self) -> int:
        return self._id


class ForgejoComment(Comment):
    def __init__(
        self,
        raw_comment: dict,
        forgejo_client: Any,
        repository: str,
        issue_number: int,
    ) -> None:
        """
        Initializes a ForgejoComment.

        Args:
            raw_comment (dict): The raw comment data.
            forgejo_client (Any): The Forgejo client instance.
            repository (str): Repository identifier (e.g., "owner/repo").
            issue_number (int): The issue number associated with the comment.
        """
        self._forgejo_client = forgejo_client
        self._repository = repository
        self._issue_number = issue_number
        self._from_raw_comment(raw_comment)

    def _from_raw_comment(self, raw_comment: dict) -> None:
        """
        Initializes comment attributes from the raw API data.
        """
        self._raw_comment = raw_comment
        self._id = raw_comment.get("id")
        self._author = raw_comment.get("user", {}).get("login")
        created_at = raw_comment.get("created_at")
        self._created = (
            datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if created_at
            else None
        )
        updated_at = raw_comment.get("updated_at")
        self._edited = (
            datetime.datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if updated_at
            else None
        )

    @property
    def body(self) -> str:
        return self._raw_comment.get("body")

    @body.setter
    def body(self, new_body: str) -> None:
        """
        Updates the comment body in Forgejo.
        """
        url = (
            f"{self._forgejo_client.forgejo_url}/api/v1/repos/"
            f"{self._repository}/issues/{self._issue_number}/comments/{self._id}"
        )
        data = {"body": new_body}
        self._forgejo_client._make_request("PATCH", url, data)
        self._raw_comment["body"] = new_body

    @property
    def edited(self) -> datetime.datetime:
        return self._edited

    def get_reactions(self) -> list[Reaction]:
        """
        Retrieves all reactions for this comment.
        """
        url = (
            f"{self._forgejo_client.forgejo_url}/api/v1/repos/"
            f"{self._repository}/issues/{self._issue_number}/comments/{self._id}/reactions"
        )
        reactions_data = self._forgejo_client._make_request("GET", url)
        return [
            ForgejoReaction(
                r,
                self._forgejo_client,
                self._repository,
                self._issue_number,
            )
            for r in reactions_data
        ]

    def add_reaction(self, reaction: str) -> ForgejoReaction:
        """
        Adds a reaction to the comment.

        Args:
            reaction (str): The reaction content (e.g., "+1", "heart").

        Returns:
            ForgejoReaction: The created reaction object.
        """
        url = (
            f"{self._forgejo_client.forgejo_url}/api/v1/repos/"
            f"{self._repository}/issues/{self._issue_number}/comments/{self._id}/reactions"
        )
        data = {"content": reaction}
        reaction_data = self._forgejo_client._make_request("POST", url, data)
        return ForgejoReaction(
            reaction_data,
            self._forgejo_client,
            self._repository,
            self._issue_number,
        )

    @property
    def id(self) -> int:
        return self._id

    @property
    def author(self) -> str:
        return self._author

    @property
    def created(self) -> datetime.datetime:
        return self._created


class ForgejoIssueComment(ForgejoComment, IssueComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()


class ForgejoPRComment(ForgejoComment, PRComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()


class ForgejoCommitComment(ForgejoComment, CommitComment):
    def __str__(self) -> str:
        return "Forgejo" + super().__str__()
