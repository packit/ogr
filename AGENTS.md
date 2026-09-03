# AGENTS.md

Instructions for anyone — human or agent — contributing to `ogr`. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide; this file
is the condensed, agent-readable version.

## What this project is

`ogr` provides one Python API for multiple git forges: GitHub, GitLab,
Pagure, and Forgejo. Consumers write forge-agnostic code against the
abstract interfaces in `ogr/abstract/`; each forge gets a concrete
implementation under `ogr/services/<forge>/`.

## Architecture

- `ogr/abstract/` — abstract base classes (`GitProject`, `GitService`,
  `PullRequest`, `Issue`, `Release`, etc.). New forge-agnostic behavior
  belongs here first, as an interface.
- `ogr/services/github/`, `ogr/services/gitlab/`, `ogr/services/pagure/`,
  `ogr/services/forgejo/` — per-forge implementations of the abstract
  interfaces.
- `ogr/factory.py` — `get_project`, `get_service_class`: forge-agnostic
  entry points that pick the right service implementation.
- `ogr/exceptions.py`, `ogr/read_only.py`, `ogr/parsing.py`, `ogr/utils.py` —
  cross-cutting concerns shared by all services.

### HTTP client convention

- GitHub, GitLab, and Pagure implementations use `requests` (via `PyGithub`,
  `python-gitlab`, and a custom `requests`-based client, respectively).
- Forgejo uses `httpx` (via `pyforgejo`).
- Keep new code for a given forge on that forge's existing library — this
  keeps test recording (see below) consistent within each service.

## Testing

- Tests live in `tests/`, and use [`requre`](https://github.com/packit/requre)
  to record/replay real HTTP responses, stored in
  `tests/integration/test_data`.
- Run locally: `make check` (requires `python3-requre` and
  `python3-flexmock` installed).
- Preferred: `make check-in-container` (requires `podman`/`docker`; build
  the image first with `make build-test-image`). Use `TEST_TARGET` to scope
  to a subset.
- If a test needs a response file that doesn't exist yet, run the test with
  the relevant real token env var set (`GITHUB_TOKEN`, `GITLAB_TOKEN`,
  `PAGURE_TOKEN`, `FORGEJO_TOKEN`, `PAGURE_OGR_TEST_TOKEN`) — it will be
  recorded automatically. Commit the generated file.
- To regenerate a stale response file, delete it and rerun (Makefile has
  `remove-response-files*` targets per service).
- Always run `pre-commit` after (re)generating response files — it purges
  volatile/sensitive fields from recordings before commit.
- CI is Zuul (`.zuul.yaml`); comment `recheck` on a PR to re-trigger it.

## Code style

- Formatting: `black`, `mdformat` (Markdown), enforced via `pre-commit`.
- Linting: `ruff` (auto-fix on commit), `mypy --no-strict-optional --ignore-missing-imports`.
- Every `.py` file needs the two-line SPDX license header (see
  `LICENSE_HEADER.txt`) — `pre-commit`'s `insert-license` hook adds it
  automatically if missing.
- Install hooks with `pre-commit install -t pre-commit -t pre-push`.

## Compatibility

If a change affects behavior across different deployed forge versions
(e.g. Pagure on `src.fedoraproject.org` vs. `pagure.io`), update
[COMPATIBILITY.md](COMPATIBILITY.md).
