# Compatibility table for services

Methods/properties not listed in here are implemented for all services.
In case you find any error, please [create a new issue](https://github.com/packit/ogr/issues/new).

## Comments

### `IssueComment`

|                  | GitHub | GitLab | Pagure | Forgejo |
| ---------------- | :----: | :----: | :----: | :-----: |
| `body` (get/set) | ✔/✔  | ✔/✔  |  ✔/✘  |   ✘/✘   |
| `add_reaction`   |   ✔   |   ✔   |   ✘    |    ✘    |
| `get_reactions`  |   ✔   |   ✔   |   ✘    |    ✘    |

### `PRComment`

|                  | GitHub | GitLab | Pagure | Forgejo |
| ---------------- | :----: | :----: | :----: | :-----: |
| `body` (get/set) | ✔/✔  | ✔/✔  |  ✔/✘  |    ✘    |
| `add_reaction`   |   ✔   |   ✔   |   ✘    |    ✘    |
| `get_reactions`  |   ✔   |   ✔   |   ✘    |    ✘    |
| `closed_by`      |   ✘    |   ✘    |   ✔   |    ✘    |

## Issue

|             | GitHub | GitLab | Pagure | Forgejo |
| ----------- | :----: | :----: | :----: | :-----: |
| `add_label` |   ✔   |   ✔   |   ✘    |    ✘    |

## Pull request

|                   | GitHub | GitLab | Pagure | Forgejo |
| ----------------- | :----: | :----: | :----: | :-----: |
| `add_label`       |   ✔   |   ✔   |   ✘    |   ✔    |
| `get_all_commits` |   ✔   |   ✔   |   ✘    |   ✔    |
| `changes`         |   ✔   |   ✘    |   ✘    |    ✘    |

## GitCommit

|           | GitHub | GitLab | Pagure | Forgejo |
| --------- | :----: | :----: | :----: | :-----: |
| `changes` |   ✔   |   ✘    |   ✘    |    ✘    |
| `get_prs` |   ✘    |   ✘    |   ✘    |    ✘    |

## Release

|                   | GitHub | GitLab |          Pagure          | Forgejo |
| ----------------- | :----: | :----: | :----------------------: | :-----: |
| `edit_release`    |   ✔   |   ✘    |            ✘             |   ✔    |
| `body` (only get) |   ✔   |   ✔   | ✘ (returns empty string) |   ✔    |

## Commit flag

|          | GitHub | GitLab | Pagure | Forgejo |
| -------- | :----: | :----: | :----: | :-----: |
| `edited` |   ✔   |   ✘    |   ✔   |    ✘    |

## Project

|                               | GitHub | GitLab |         Pagure          | Forgejo |
| ----------------------------- | :----: | :----: | :---------------------: | :-----: |
| `change_token`                |   ✘    |   ✔   |           ✔            |    ✘    |
| `get_release`                 |   ✔   |   ✔   |            ✘            |    ✘    |
| `get_commits`                 |   ✔   |   ✔   |            ✘            |   ✔    |
| `get_latest_release`          |   ✔   |   ✔   |            ✘            |    ✘    |
| `is_private`                  |   ✔   |   ✔   | ✘ (may not be accurate) |   ✔    |
| `remove_user`                 |   ✘    |   ✘    |           ✔            |   ✔    |
| `add_group`                   |   ✘    |   ✘    |           ✔            |    ✘    |
| `remove_group`                |   ✘    |   ✘    |           ✔            |    ✘    |
| `which_groups_can_merge_pr`   |   ✘    |   ✘    |           ✔            |    ✘    |
| `get_pr_files_diff`           |   ✘    |   ✘    |           ✔            |    ✘    |
| `get_users_with_given_access` |   ✘    |   ✘    |           ✔            |   ✔    |
| `get_commit`                  |   ✔   |   ✘    |            ✘            |    ✘    |

## User

|                | GitHub | GitLab | Pagure | Forgejo |
| -------------- | :----: | :----: | :----: | :-----: |
| `get_projects` |   ✔   |   ✘    |   ✔   |   ✔    |
| `get_forks`    |   ✔   |   ✘    |   ✔   |   ✔    |
| `get_email`    |   ✔   |   ✔   |   ✘    |   ✔    |

## Reaction

|          | GitHub | GitLab | Pagure | Forgejo |
| -------- | :----: | :----: | :----: | :-----: |
| `delete` |   ✔   |   ✔   |   ✘    |    ✘    |

## Service

|             | GitHub | GitLab | Pagure | Forgejo |
| ----------- | :----: | :----: | :----: | :-----: |
| `get_group` |   ✘    |   ✘    |   ✔   |    ✘    |
