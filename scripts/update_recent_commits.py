#!/usr/bin/env python3
"""Update profile activity from verified public GitHub commits.

Scan up to 20 public, non-disabled repositories owned by --user, ordered by
their latest push. Forks are included; the user's profile repository is not.
Read five matching commits from each default branch and display the newest
five by author timestamp, deduplicated by SHA. This bounded scan is not a
complete account-wide history. Repository listing paginates up to 1,000 repos.

GITHUB_TOKEN is optional. API/validation failures leave all output unchanged.
Both READMEs need exactly one RECENT_COMMITS:START / RECENT_COMMITS:END pair.
No generation timestamp is stored, so unchanged activity produces no diff.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


API_VERSION = "2026-03-10"
REPOSITORY_LIMIT = 20
COMMITS_PER_REPOSITORY = 5
DISPLAY_LIMIT = 5
MAX_REPOSITORY_PAGES = 10
DISPLAY_TIMEZONE = timezone(timedelta(hours=8))
START_MARKER = "<!--RECENT_COMMITS:START-->"
END_MARKER = "<!--RECENT_COMMITS:END-->"
README_NAMES = ("README.md", "README.zh-CN.md")

# Ignore known generated profile artifacts, not all "sync", "update", or
# "[skip ci]" commits. Human commits made through GitHub's web-flow are valid.
AUTOMATED_ARTIFACT_UPDATE = re.compile(
    r"^(?:(?:chore|ci)(?:\((?:profile|readme|metrics|stats|activity|contributions)\))?:\s*)?"
    r"(?:update|sync|generate|regenerate)\s+(?:generated\s+)?"
    r"(?:github[- ]metrics|profile metrics|readme stats|"
    r"contribution (?:graph|grid|snake)|recent (?:commits|activity)|"
    r"profile[- ]3d[- ]contrib|github[- ]contribution[- ]grid[- ]snake)\b",
    re.IGNORECASE,
)


class UpdateError(Exception):
    """A failed fetch or invalid input that must not replace last good output."""


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token

    def get_json(self, path: str, *, allow_empty: bool = False):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "github-profile-recent-commits",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request("https://api.github.com" + path, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if allow_empty and error.code == 409:
                try:
                    detail = json.loads(error.read()).get("message", "")
                except (ValueError, AttributeError):
                    detail = ""
                if isinstance(detail, str) and detail.rstrip(".").casefold() in {
                    "git repository is empty", "repository is empty"
                }:
                    return []
            raise UpdateError(f"GitHub API returned HTTP {error.code} for {path}") from error
        except (URLError, TimeoutError, OSError, ValueError) as error:
            raise UpdateError(f"Could not read GitHub API response for {path}: {error}") from error


def validate_user(user: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", user):
        raise UpdateError("--user must be a GitHub username")


def public_repositories(client, user: str) -> list[dict]:
    """Return the first eligible repositories in GitHub's pushed-desc order."""
    repositories = []
    seen = set()
    for page in range(1, MAX_REPOSITORY_PAGES + 1):
        query = urlencode({
            "type": "owner", "sort": "pushed", "direction": "desc",
            "per_page": 100, "page": page,
        })
        response = client.get_json(f"/users/{quote(user)}/repos?{query}")
        if not isinstance(response, list):
            raise UpdateError("GitHub repository response must be a list")
        for repository in response:
            if not isinstance(repository, dict):
                raise UpdateError("Invalid GitHub repository record")
            owner = repository.get("owner") or {}
            if (
                repository.get("private") is not False
                or repository.get("visibility", "public") != "public"
                or repository.get("disabled") is not False
                or not isinstance(owner, dict)
                or str(owner.get("login", "")).casefold() != user.casefold()
            ):
                continue
            name = repository.get("name", "")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
                raise UpdateError("Invalid public repository name")
            if name.casefold() == user.casefold():
                continue  # Never turn profile-generated commits into more activity.
            full_name = repository.get("full_name")
            if full_name != f"{owner['login']}/{name}":
                raise UpdateError("Repository ownership does not match its full name")
            if full_name.casefold() in seen:
                continue
            if not isinstance(repository.get("default_branch"), str) or not repository["default_branch"]:
                raise UpdateError(f"No default branch supplied for {full_name}")
            if not isinstance(repository.get("fork"), bool):
                raise UpdateError(f"Missing fork status for {full_name}")
            seen.add(full_name.casefold())
            repositories.append(repository)
            if len(repositories) == REPOSITORY_LIMIT:
                return repositories
        if len(response) < 100:
            return repositories
    raise UpdateError("Repository listing exceeded 1,000 entries; refusing an incomplete listing")


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise UpdateError("Missing commit author timestamp")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise UpdateError("Invalid commit author timestamp") from error
    if timestamp.tzinfo is None:
        raise UpdateError("Commit timestamp must include a timezone")
    return timestamp.astimezone(timezone.utc)


def is_generated_update(title: str) -> bool:
    # Skip markers alone are not evidence of automation.
    untagged = re.sub(r"\[(?:skip ci|ci skip|skip actions|actions skip)\]", "", title, flags=re.I).strip()
    return bool(AUTOMATED_ARTIFACT_UPDATE.match(untagged))


def authored_commit(repository: dict, raw: dict, user: str) -> dict | None:
    if not isinstance(raw, dict):
        raise UpdateError("Invalid GitHub commit record")
    author = raw.get("author") or {}
    if (
        not isinstance(author, dict)
        or author.get("type") != "User"
        or str(author.get("login", "")).casefold() != user.casefold()
    ):
        return None
    commit = raw.get("commit")
    if not isinstance(commit, dict) or not isinstance(commit.get("message"), str):
        raise UpdateError("Missing commit message")
    title = commit["message"].splitlines()[0] if commit["message"].splitlines() else ""
    if is_generated_update(title):
        return None
    sha = raw.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise UpdateError("Invalid commit SHA")
    commit_author = commit.get("author") or {}
    if not isinstance(commit_author, dict):
        raise UpdateError("Missing commit author metadata")
    authored_at = parse_timestamp(commit_author.get("date"))
    url = f"https://github.com/{repository['full_name']}/commit/{sha}"
    if raw.get("html_url") != url:
        raise UpdateError("Commit URL does not match the verified repository and SHA")
    return {
        "repository": repository["full_name"],
        "default_branch": repository["default_branch"],
        "is_fork": repository["fork"],
        "sha": sha,
        "url": url,
        "title": title,
        "author": author["login"],
        "authored_at": authored_at.isoformat().replace("+00:00", "Z"),
    }


def collect_commits(client, user: str) -> list[dict]:
    commits = []
    for repository in public_repositories(client, user):
        query = urlencode({
            "author": user,
            "sha": repository["default_branch"],
            "per_page": COMMITS_PER_REPOSITORY,
        })
        response = client.get_json(
            f"/repos/{repository['full_name']}/commits?{query}", allow_empty=True
        )
        if not isinstance(response, list):
            raise UpdateError(f"Commit response for {repository['full_name']} must be a list")
        for raw in response:
            commit = authored_commit(repository, raw, user)
            if commit is not None:
                commits.append(commit)
    # Prefer the original repository when the same authored commit is mirrored
    # in an owned fork. Stable tie breaking avoids needless generated diffs.
    commits.sort(key=lambda commit: (
        -parse_timestamp(commit["authored_at"]).timestamp(),
        commit["is_fork"], commit["repository"].casefold(), commit["sha"],
    ))
    selected = []
    seen_shas = set()
    for commit in commits:
        if commit["sha"] not in seen_shas:
            selected.append(commit)
            seen_shas.add(commit["sha"])
        if len(selected) == DISPLAY_LIMIT:
            break
    return selected


def escape_title(title: str) -> str:
    """Keep source-language titles; remove controls and escape Markdown/HTML."""
    visible = "".join(character for character in title if unicodedata.category(character) not in {"Cc", "Cf", "Zl", "Zp"}).strip()
    if not visible:
        visible = "Untitled commit"
    if len(visible) > 160:
        visible = visible[:159] + "…"
    escaped = html.escape(visible, quote=False)
    return "".join("\\" + character if character in "\\`*_{}[]()#+-.!|~" else character for character in escaped)


def render_activity(commits: list[dict]) -> str:
    lines = []
    for commit in commits:
        date = parse_timestamp(commit["authored_at"]).astimezone(DISPLAY_TIMEZONE).strftime("%Y-%m-%d")
        lines.append(
            f"- `{date}` `{commit['repository']}` · "
            f"[`{commit['sha'][:7]}`]({commit['url']}) — "
            f"[{escape_title(commit['title'])}]({commit['url']})"
        )
    if not lines:
        lines.append("No matching public commits found in the scanned repositories.")
    lines.extend([
        "",
        f"<sub>Dates: UTC+08:00 · Up to {REPOSITORY_LIMIT} recently pushed public repositories scanned · Default branches only.</sub>",
    ])
    return "\n".join(lines)


def replace_activity(content: str, block: str, name: str) -> str:
    if content.count(START_MARKER) != 1 or content.count(END_MARKER) != 1:
        raise UpdateError(f"{name} needs exactly one recent-commits marker pair")
    start = content.index(START_MARKER) + len(START_MARKER)
    end = content.index(END_MARKER)
    if start > end:
        raise UpdateError(f"{name} has reversed recent-commits markers")
    newline = "\r\n" if "\r\n" in content else "\n"
    return content[:start] + newline + block.replace("\n", newline) + newline + content[end:]


def write_changed_files(outputs: dict[Path, bytes]) -> list[Path]:
    changed = {path: value for path, value in outputs.items() if not path.exists() or path.read_bytes() != value}
    staged = []
    try:
        for path, value in changed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as temporary:
                staged.append((Path(temporary.name), path))
                temporary.write(value)
            os.chmod(temporary.name, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        for temporary, path in staged:
            os.replace(temporary, path)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return list(changed)


def update_profile(root: Path, user: str, client) -> list[Path]:
    validate_user(user)
    readmes = {}
    for name in README_NAMES:
        path = root / name
        content = path.read_bytes().decode("utf-8")
        replace_activity(content, "", name)  # Validate every destination before fetching.
        readmes[path] = content
    commits = collect_commits(client, user)
    block = render_activity(commits)
    outputs = {
        path: replace_activity(content, block, path.name).encode("utf-8")
        for path, content in readmes.items()
    }
    data = {
        "schema_version": 1,
        "user": user,
        "display_timezone": "UTC+08:00",
        "scan": {
            "repository_limit": REPOSITORY_LIMIT,
            "commits_per_repository": COMMITS_PER_REPOSITORY,
            "display_limit": DISPLAY_LIMIT,
            "scope": "Public owned repositories, including forks; default branches only; profile repository excluded",
            "ordering": "Author timestamp, newest first",
            "filters": "Matching GitHub user authors only; bots and generated profile-artifact updates excluded",
        },
        "commits": commits,
    }
    outputs[root / "data" / "recent-commits.json"] = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return write_changed_files(outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", default="DapengFeng", help="GitHub username (default: DapengFeng)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Repository root containing both READMEs")
    args = parser.parse_args(argv)
    try:
        changed = update_profile(args.root, args.user, GitHubClient(os.environ.get("GITHUB_TOKEN")))
    except (UpdateError, OSError, UnicodeError) as error:
        print(f"Recent commits update failed: {error}", file=sys.stderr)
        return 1
    print(f"Updated {len(changed)} file(s)." if changed else "Recent commits unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
