"""Offline behavioral checks for public activity selection and safe updates."""

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


SPEC = importlib.util.spec_from_file_location(
    "recent_commits", Path(__file__).resolve().parents[1] / "scripts" / "update_recent_commits.py"
)
activity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activity)
USER = "DapengFeng"


def repository(name="project", **overrides):
    value = {
        "name": name, "full_name": f"{USER}/{name}", "owner": {"login": USER},
        "private": False, "visibility": "public", "disabled": False,
        "fork": False, "default_branch": "main",
    }
    value.update(overrides)
    return value


def commit(repo, number=1, date="2026-10-09T17:00:00Z", title="Fix camera calibration", **overrides):
    sha = f"{number:040x}"
    value = {
        "sha": sha, "html_url": f"https://github.com/{repo['full_name']}/commit/{sha}",
        "author": {"login": USER, "type": "User"},
        "committer": {"login": "web-flow", "type": "Bot"},
        "commit": {"message": title, "author": {"date": date}},
    }
    value.update(overrides)
    return value


class FakeClient:
    def __init__(self, repos, commits=None, fail_repo=None, pages=None):
        self.repos = repos
        self.commits = commits or {}
        self.fail_repo = fail_repo
        self.pages = pages
        self.calls = []

    def get_json(self, path, *, allow_empty=False):
        self.calls.append((path, allow_empty))
        url = urlsplit(path)
        query = parse_qs(url.query)
        if url.path == f"/users/{USER}/repos":
            if self.pages is not None:
                return self.pages[int(query["page"][0]) - 1]
            return self.repos
        name = url.path.removeprefix("/repos/").removesuffix("/commits")
        if name == self.fail_repo:
            raise activity.UpdateError("simulated rate limit")
        return self.commits.get(name, [])


class RecentCommitsTests(unittest.TestCase):
    def test_only_owned_public_enabled_repos_and_explicit_default_branch(self):
        fork = repository("fork", fork=True, default_branch="feature/docs")
        rejected = [
            repository(USER), repository("private", private=True),
            repository("internal", visibility="internal"),
            repository("disabled", disabled=True),
            repository("other", owner={"login": "someone"}, full_name="someone/other"),
        ]
        client = FakeClient(rejected + [fork], {fork["full_name"]: [commit(fork)]})
        result = activity.collect_commits(client, USER)
        self.assertEqual([item["repository"] for item in result], [fork["full_name"]])
        self.assertTrue(result[0]["is_fork"])
        self.assertEqual(len(client.calls), 2)
        listing = parse_qs(urlsplit(client.calls[0][0]).query)
        self.assertEqual(listing["type"], ["owner"])
        self.assertEqual(listing["sort"], ["pushed"])
        self.assertEqual(listing["direction"], ["desc"])
        query = parse_qs(urlsplit(client.calls[1][0]).query)
        self.assertEqual(query, {"author": [USER], "sha": ["feature/docs"], "per_page": ["5"]})

    def test_pagination_and_scan_limit(self):
        excluded = [repository(f"private-{i}", private=True) for i in range(100)]
        eligible = [repository(f"repo-{i}") for i in range(25)]
        client = FakeClient([], pages=[excluded, eligible])
        self.assertEqual(len(activity.public_repositories(client, USER)), 20)
        self.assertEqual(len(client.calls), 2)

    def test_author_validation_bot_filter_and_narrow_automation_filter(self):
        repo = repository()
        records = [
            commit(repo, 1, author={"login": "someone", "type": "User"}),
            commit(repo, 2, author={"login": USER, "type": "Bot"}),
            commit(repo, 3, author=None),
            commit(repo, 4, title="chore: update recent commits [skip ci]"),
            commit(repo, 5, title="Sync sensor timestamps"),
            commit(repo, 6, title="docs: explain calibration [skip ci]"),
        ]
        client = FakeClient([repo], {repo["full_name"]: records})
        selected = activity.collect_commits(client, USER)
        self.assertEqual({item["sha"] for item in selected}, {f"{5:040x}", f"{6:040x}"})

    def test_newest_five_are_sorted_by_author_time_and_shas_deduplicated(self):
        main = repository("original")
        fork = repository("fork", fork=True)
        records = [commit(main, i, date=f"2026-10-{i:02}T00:00:00Z") for i in range(1, 8)]
        client = FakeClient([fork, main], {
            main["full_name"]: records,
            fork["full_name"]: [commit(fork, 7, date="2026-10-07T00:00:00Z")],
        })
        selected = activity.collect_commits(client, USER)
        self.assertEqual([int(item["sha"], 16) for item in selected], [7, 6, 5, 4, 3])
        self.assertEqual(selected[0]["repository"], main["full_name"])

    def test_titles_cannot_inject_html_markdown_or_bidi_controls(self):
        repo = repository()
        title = '<script>alert(1)</script> [click](javascript:bad) ![x](evil) `x` \\ **bold** \u202eevil'
        record = activity.authored_commit(repo, commit(repo, title=title + "\nSecret body"), USER)
        rendered = activity.render_activity([record])
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("[click](javascript:bad)", rendered)
        self.assertNotIn("![x](evil)", rendered)
        self.assertNotIn("\u202e", rendered)
        self.assertNotIn("Secret body", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn(r"\[click\]\(javascript:bad\)", rendered)

    def test_utc_plus_eight_date_and_original_language(self):
        repo = repository()
        record = activity.authored_commit(repo, commit(repo, title="修复相机标定"), USER)
        rendered = activity.render_activity([record])
        self.assertIn("`2026-10-10`", rendered)
        self.assertIn("修复相机标定", rendered)
        self.assertIn("UTC+08:00", rendered)
        self.assertIn("20 recently pushed public repositories", rendered)

    def make_root(self, directory):
        root = Path(directory)
        for name in activity.README_NAMES:
            (root / name).write_text(
                f"before\n{activity.START_MARKER}\nlast good activity\n{activity.END_MARKER}\nafter\n",
                encoding="utf-8",
            )
        (root / "data").mkdir()
        (root / "data" / "recent-commits.json").write_text('{"last": "good"}\n')
        return root

    def snapshot(self, root):
        return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}

    def test_api_failure_preserves_every_last_good_output(self):
        first, second = repository("first"), repository("second")
        client = FakeClient([first, second], {first["full_name"]: [commit(first)]}, fail_repo=second["full_name"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_root(directory)
            before = self.snapshot(root)
            with self.assertRaisesRegex(activity.UpdateError, "rate limit"):
                activity.update_profile(root, USER, client)
            self.assertEqual(self.snapshot(root), before)

    def test_missing_duplicate_reversed_markers_preserve_output(self):
        invalid = [
            "no markers", activity.START_MARKER + activity.START_MARKER + activity.END_MARKER,
            activity.END_MARKER + activity.START_MARKER,
        ]
        for content in invalid:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                root = self.make_root(directory)
                (root / "README.zh-CN.md").write_text(content)
                before = self.snapshot(root)
                client = FakeClient([])
                with self.assertRaises(activity.UpdateError):
                    activity.update_profile(root, USER, client)
                self.assertEqual(self.snapshot(root), before)
                self.assertEqual(client.calls, [])

    def test_success_updates_both_readmes_and_data_without_repeat_writes(self):
        repo = repository()
        client = FakeClient([repo], {repo["full_name"]: [commit(repo)]})
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_root(directory)
            changed = activity.update_profile(root, USER, client)
            self.assertEqual(len(changed), 3)
            for name in activity.README_NAMES:
                text = (root / name).read_text()
                self.assertTrue(text.startswith("before\n"))
                self.assertTrue(text.endswith("after\n"))
                self.assertIn("Fix camera calibration", text)
            data = json.loads((root / "data" / "recent-commits.json").read_text())
            self.assertEqual(data["commits"][0]["author"], USER)
            self.assertNotIn("generated_at", data)
            mtimes = {path: path.stat().st_mtime_ns for path in changed}
            self.assertEqual(activity.update_profile(root, USER, client), [])
            self.assertEqual({path: path.stat().st_mtime_ns for path in changed}, mtimes)

    def test_empty_state_and_crlf_preserve_surrounding_text(self):
        rendered = activity.render_activity([])
        self.assertIn("No matching public commits", rendered)
        source = f"before\r\n{activity.START_MARKER}\r\nold\r\n{activity.END_MARKER}\r\nafter\r\n"
        result = activity.replace_activity(source, rendered, "README.md")
        self.assertNotIn("\n", result.replace("\r\n", ""))
        self.assertTrue(result.endswith("after\r\n"))

    def test_untrusted_commit_url_fails_validation(self):
        repo = repository()
        with self.assertRaisesRegex(activity.UpdateError, "URL"):
            activity.authored_commit(repo, commit(repo, html_url="javascript:alert(1)"), USER)

    def test_only_known_empty_repository_409_is_allowed(self):
        for message, allowed in [("Git Repository is empty.", True), ("Conflict", False)]:
            error = HTTPError("https://api.github.com/test", 409, "Conflict", {}, io.BytesIO(json.dumps({"message": message}).encode()))
            with self.subTest(message=message), patch.object(activity, "urlopen", side_effect=error):
                if allowed:
                    self.assertEqual(activity.GitHubClient().get_json("/test", allow_empty=True), [])
                else:
                    with self.assertRaises(activity.UpdateError):
                        activity.GitHubClient().get_json("/test", allow_empty=True)

    def test_api_version_header_and_optional_token(self):
        response = io.BytesIO(b"[]")
        with patch.object(activity, "urlopen", return_value=response) as opened:
            activity.GitHubClient("example-token").get_json("/test")
        request = opened.call_args.args[0]
        self.assertEqual(request.get_header("X-github-api-version"), "2026-03-10")
        self.assertEqual(request.get_header("Authorization"), "Bearer example-token")


if __name__ == "__main__":
    unittest.main()
