# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from typing import Any, Optional, TypeVar, Union

from ogr.abstract.abstract_class import OgrAbstractClass
from ogr.abstract.issue import Issue
from ogr.abstract.pull_request import PullRequest
from ogr.deprecation import deprecate_and_set_removal

AnyComment = TypeVar("AnyComment", bound="Comment")


class Reaction(OgrAbstractClass):
    def __init__(self, raw_reaction: Any) -> None:
        self._raw_reaction = raw_reaction

    def __str__(self):
        return f"Reaction(raw_reaction={self._raw_reaction})"

    def delete(self) -> None:
        """Delete a reaction."""
        raise NotImplementedError()


class Comment(OgrAbstractClass):
    def __init__(
        self,
        raw_comment: Optional[Any] = None,
        parent: Optional[Any] = None,
        body: Optional[str] = None,
        id_: Optional[int] = None,
        author: Optional[str] = None,
        created: Optional[datetime.datetime] = None,
        edited: Optional[datetime.datetime] = None,
    ) -> None:
        if raw_comment:
            self._from_raw_comment(raw_comment)
        elif body and author:
            self._body = body
            self._id = id_
            self._author = author
            self._created = created
            self._edited = edited
        else:
            raise ValueError("cannot construct comment without body and author")

        self._parent = parent

    def __str__(self) -> str:
        body = f"{self.body[:10]}..." if self.body is not None else "None"
        return (
            f"Comment("
            f"comment='{body}', "
            f"author='{self.author}', "
            f"created='{self.created}', "
            f"edited='{self.edited}')"
        )

    def _from_raw_comment(self, raw_comment: Any) -> None:
        """Constructs Comment object from raw_comment given from API."""
        raise NotImplementedError()

    @property
    def body(self) -> str:
        """Body of the comment."""
        return self._body

    @body.setter
    def body(self, new_body: str) -> None:
        self._body = new_body

    @property
    def id(self) -> int:
        return self._id

    @property
    def author(self) -> str:
        """Login of the author of the comment."""
        return self._author

    @property
    def created(self) -> datetime.datetime:
        """Datetime of creation of the comment."""
        return self._created

    @property
    def edited(self) -> datetime.datetime:
        """Datetime of last edit of the comment."""
        return self._edited

    def get_reactions(self) -> Union[list[Reaction], Iterable[Reaction]]:
        """Returns list of reactions."""
        raise NotImplementedError()

    def add_reaction(self, reaction: str) -> Reaction:
        """
        Reacts to a comment.

        Colons in between reaction are not needed, e.g. `comment.add_reaction("+1")`.

        Args:
            reaction: String representing specific reaction to be added.

        Returns:
            Object representing newly added reaction.
        """
        raise NotImplementedError()


class IssueComment(Comment):
    @property
    def issue(self) -> "Issue":
        """Issue of issue comment."""
        return self._parent

    def __str__(self) -> str:
        return "Issue" + super().__str__()


class CommitComment(Comment):
    """
    Attributes:
        sha (str): Hash of the related commit.
        body (str): Body of the comment.
        author (str): Login of the author.
    """

    def __init__(
        self,
        sha: str,
        raw_comment: Any,
    ) -> None:
        super().__init__(raw_comment=raw_comment)
        self.sha = sha

    @property  # type: ignore
    @deprecate_and_set_removal(
        since="0.41.0",
        remove_in="0.46.0 (or 1.0.0 if it comes sooner)",
        message="Use body",
    )
    def comment(self) -> str:
        return self.body

    def __str__(self) -> str:
        return (
            f"CommitComment(commit={self.sha}, author={self.author}, body={self.body})"
        )


class PRComment(Comment):
    @property
    def pull_request(self) -> "PullRequest":
        """Pull request of pull request comment."""
        return self._parent

    def __str__(self) -> str:
        return "PR" + super().__str__()
