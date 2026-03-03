"""
sentry-errors - Sentry error monitoring integration

A SkillGuard official skill for pulling full error context from Sentry:
stack traces, breadcrumbs, user context, and issue management.
Upstream: https://mcp.sentry.dev
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class SentryErrorsSkill(Skill):
    """Sentry error monitoring skill."""

    _BASE_URL = "https://sentry.io/api/0"

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "list_issues": self._list_issues,
            "get_issue": self._get_issue,
            "get_latest_event": self._get_latest_event,
            "resolve_issue": self._resolve_issue,
            "list_projects": self._list_projects,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _headers(self, context: SkillContext):
        token = (os.environ.get("SENTRY_AUTH_TOKEN") or
                 context.secrets.get("SENTRY_AUTH_TOKEN"))
        if not token:
            return None, None, SkillResult.error("SENTRY_AUTH_TOKEN not set")

        org = (os.environ.get("SENTRY_ORG") or
               context.secrets.get("SENTRY_ORG"))
        if not org:
            return None, None, SkillResult.error("SENTRY_ORG not set")

        return {"Authorization": f"Bearer {token}"}, org, None

    def _list_issues(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        headers, org, err = self._headers(context)
        if err:
            return err

        project = context.parameters.get("project")
        if not project:
            return SkillResult.error("Missing required parameter: project")

        query = context.parameters.get("query", "is:unresolved")
        limit = min(context.parameters.get("limit", 25), 100)

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(
                    f"{self._BASE_URL}/projects/{org}/{project}/issues/",
                    headers=headers,
                    params={"query": query, "limit": limit},
                )
                resp.raise_for_status()
                issues = [{"id": i["id"], "title": i["title"],
                           "count": i.get("count"), "user_count": i.get("userCount"),
                           "first_seen": i.get("firstSeen"),
                           "last_seen": i.get("lastSeen"),
                           "status": i.get("status")}
                          for i in resp.json()]
                return SkillResult.success(issues, count=len(issues))
        except Exception as e:
            return SkillResult.error(f"Sentry error: {e}")

    def _get_issue(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        issue_id = context.parameters.get("issue_id")
        if not issue_id:
            return SkillResult.error("Missing required parameter: issue_id")

        headers, _, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/issues/{issue_id}/",
                                  headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return SkillResult.success({
                    "id": data["id"],
                    "title": data["title"],
                    "culprit": data.get("culprit"),
                    "status": data.get("status"),
                    "count": data.get("count"),
                    "user_count": data.get("userCount"),
                    "first_seen": data.get("firstSeen"),
                    "last_seen": data.get("lastSeen"),
                    "tags": data.get("tags", []),
                    "metadata": data.get("metadata", {}),
                })
        except Exception as e:
            return SkillResult.error(f"Sentry error: {e}")

    def _get_latest_event(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        issue_id = context.parameters.get("issue_id")
        if not issue_id:
            return SkillResult.error("Missing required parameter: issue_id")

        headers, _, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/issues/{issue_id}/events/latest/",
                                  headers=headers)
                resp.raise_for_status()
                data = resp.json()

                exception = None
                for entry in data.get("entries", []):
                    if entry.get("type") == "exception":
                        exception = entry.get("data")
                        break

                return SkillResult.success({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "datetime": data.get("dateCreated"),
                    "exception": exception,
                    "tags": {t["key"]: t["value"] for t in data.get("tags", [])},
                    "user": data.get("user"),
                    "request": data.get("request"),
                    "sdk": data.get("sdk"),
                    "platform": data.get("platform"),
                })
        except Exception as e:
            return SkillResult.error(f"Sentry error: {e}")

    def _resolve_issue(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        issue_id = context.parameters.get("issue_id")
        if not issue_id:
            return SkillResult.error("Missing required parameter: issue_id")

        headers, _, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_resolve=issue_id)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.put(f"{self._BASE_URL}/issues/{issue_id}/",
                                  headers=headers, json={"status": "resolved"})
                resp.raise_for_status()
                data = resp.json()
                return SkillResult.success({"id": data["id"], "status": data.get("status")})
        except Exception as e:
            return SkillResult.error(f"Sentry error: {e}")

    def _list_projects(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        headers, org, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/organizations/{org}/projects/",
                                  headers=headers)
                resp.raise_for_status()
                projects = [{"id": p["id"], "name": p["name"],
                             "slug": p["slug"], "platform": p.get("platform")}
                            for p in resp.json()]
                return SkillResult.success(projects, count=len(projects))
        except Exception as e:
            return SkillResult.error(f"Sentry error: {e}")


def create_skill() -> SentryErrorsSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return SentryErrorsSkill(manifest)
