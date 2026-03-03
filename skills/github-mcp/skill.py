"""
github-mcp - GitHub API operations for AI agents

A SkillGuard official skill wrapping the GitHub REST API for repository,
issue, pull request, and code search operations.
Upstream: https://github.com/github/github-mcp-server
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class GitHubMCPSkill(Skill):
    """GitHub API operations skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "list_repos": self._list_repos,
            "get_repo": self._get_repo,
            "list_issues": self._list_issues,
            "create_issue": self._create_issue,
            "list_prs": self._list_prs,
            "create_pr": self._create_pr,
            "get_file_contents": self._get_file_contents,
            "search_code": self._search_code,
            "search_issues": self._search_issues,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _client(self, context: SkillContext):
        try:
            import httpx
        except ImportError:
            return None, SkillResult.error("httpx not installed")

        token = os.environ.get("GITHUB_TOKEN") or context.secrets.get("GITHUB_TOKEN")
        if not token:
            return None, SkillResult.error("GITHUB_TOKEN not set")

        client = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=context.timeout_seconds,
        )
        return client, None

    def _list_repos(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        if not owner:
            return SkillResult.error("Missing required parameter: owner")

        repo_type = context.parameters.get("type", "all")

        if context.dry_run:
            return SkillResult.success([], dry_run=True, would_query=f"repos for {owner}")

        try:
            with client:
                resp = client.get(f"/users/{owner}/repos", params={"type": repo_type, "per_page": 100})
                resp.raise_for_status()
                repos = [{"name": r["name"], "description": r["description"],
                          "stars": r["stargazers_count"], "language": r["language"],
                          "url": r["html_url"]} for r in resp.json()]
                return SkillResult.success(repos, count=len(repos))
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _get_repo(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        if not owner or not repo:
            return SkillResult.error("Missing required parameters: owner, repo")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_query=f"{owner}/{repo}")

        try:
            with client:
                resp = client.get(f"/repos/{owner}/{repo}")
                resp.raise_for_status()
                r = resp.json()
                return SkillResult.success({
                    "name": r["name"], "full_name": r["full_name"],
                    "description": r["description"], "stars": r["stargazers_count"],
                    "forks": r["forks_count"], "language": r["language"],
                    "default_branch": r["default_branch"], "url": r["html_url"],
                    "clone_url": r["clone_url"], "topics": r["topics"],
                    "open_issues": r["open_issues_count"],
                })
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _list_issues(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        if not owner or not repo:
            return SkillResult.error("Missing required parameters: owner, repo")

        state = context.parameters.get("state", "open")
        labels = context.parameters.get("labels", "")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with client:
                params = {"state": state, "per_page": 50}
                if labels:
                    params["labels"] = labels
                resp = client.get(f"/repos/{owner}/{repo}/issues", params=params)
                resp.raise_for_status()
                issues = [{"number": i["number"], "title": i["title"],
                           "state": i["state"], "labels": [l["name"] for l in i["labels"]],
                           "url": i["html_url"], "created_at": i["created_at"]}
                          for i in resp.json() if "pull_request" not in i]
                return SkillResult.success(issues, count=len(issues))
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _create_issue(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        title = context.parameters.get("title")
        if not all([owner, repo, title]):
            return SkillResult.error("Missing required parameters: owner, repo, title")

        body = context.parameters.get("body", "")
        labels = context.parameters.get("labels", [])

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_create=title)

        try:
            with client:
                payload = {"title": title, "body": body}
                if labels:
                    payload["labels"] = labels
                resp = client.post(f"/repos/{owner}/{repo}/issues", json=payload)
                resp.raise_for_status()
                i = resp.json()
                return SkillResult.success({"number": i["number"], "url": i["html_url"]})
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _list_prs(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        if not owner or not repo:
            return SkillResult.error("Missing required parameters: owner, repo")

        state = context.parameters.get("state", "open")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with client:
                resp = client.get(f"/repos/{owner}/{repo}/pulls",
                                  params={"state": state, "per_page": 50})
                resp.raise_for_status()
                prs = [{"number": p["number"], "title": p["title"],
                        "state": p["state"], "head": p["head"]["ref"],
                        "base": p["base"]["ref"], "url": p["html_url"],
                        "draft": p["draft"]} for p in resp.json()]
                return SkillResult.success(prs, count=len(prs))
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _create_pr(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        title = context.parameters.get("title")
        head = context.parameters.get("head")
        base = context.parameters.get("base", "main")
        if not all([owner, repo, title, head]):
            return SkillResult.error("Missing required parameters: owner, repo, title, head")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_create=f"{head} -> {base}")

        try:
            with client:
                payload = {"title": title, "head": head, "base": base,
                           "body": context.parameters.get("body", "")}
                resp = client.post(f"/repos/{owner}/{repo}/pulls", json=payload)
                resp.raise_for_status()
                p = resp.json()
                return SkillResult.success({"number": p["number"], "url": p["html_url"]})
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _get_file_contents(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        owner = context.parameters.get("owner")
        repo = context.parameters.get("repo")
        path = context.parameters.get("path")
        if not all([owner, repo, path]):
            return SkillResult.error("Missing required parameters: owner, repo, path")

        ref = context.parameters.get("ref")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            import base64
            with client:
                params = {}
                if ref:
                    params["ref"] = ref
                resp = client.get(f"/repos/{owner}/{repo}/contents/{path}", params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                else:
                    content = data.get("content", "")
                return SkillResult.success({
                    "path": data["path"], "size": data["size"],
                    "sha": data["sha"], "content": content,
                })
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _search_code(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with client:
                resp = client.get("/search/code", params={"q": query, "per_page": 30})
                resp.raise_for_status()
                data = resp.json()
                results = [{"path": i["path"], "repo": i["repository"]["full_name"],
                            "url": i["html_url"]} for i in data.get("items", [])]
                return SkillResult.success(results, total=data.get("total_count", 0))
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")

    def _search_issues(self, context: SkillContext) -> SkillResult:
        client, err = self._client(context)
        if err:
            return err

        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with client:
                resp = client.get("/search/issues", params={"q": query, "per_page": 30})
                resp.raise_for_status()
                data = resp.json()
                results = [{"number": i["number"], "title": i["title"],
                            "state": i["state"], "url": i["html_url"],
                            "repo": i["repository_url"].split("/repos/")[-1]}
                           for i in data.get("items", [])]
                return SkillResult.success(results, total=data.get("total_count", 0))
        except Exception as e:
            return SkillResult.error(f"GitHub API error: {e}")


def create_skill() -> GitHubMCPSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return GitHubMCPSkill(manifest)
