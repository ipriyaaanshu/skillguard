"""
brave-search - Privacy-first web and news search

A SkillGuard official skill wrapping the Brave Search API for real-time
web and news search without Google/Bing dependency.
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class BraveSearchSkill(Skill):
    """Brave Search API skill."""

    _BASE_URL = "https://api.search.brave.com/res/v1"

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "search": self._search,
            "search_news": self._search_news,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _get_headers(self, context: SkillContext):
        api_key = os.environ.get("BRAVE_API_KEY") or context.secrets.get("BRAVE_API_KEY")
        if not api_key:
            return None, SkillResult.error("BRAVE_API_KEY not set")
        return {"Accept": "application/json", "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key}, None

    def _search(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        count = min(context.parameters.get("count", 10), 20)
        freshness = context.parameters.get("freshness")

        headers, err = self._get_headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_search=query)

        try:
            params = {"q": query, "count": count}
            if freshness:
                params["freshness"] = freshness

            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/web/search", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

                web_results = [
                    {"title": r.get("title"), "url": r.get("url"),
                     "description": r.get("description")}
                    for r in data.get("web", {}).get("results", [])
                ]
                news_results = [
                    {"title": r.get("title"), "url": r.get("url"),
                     "description": r.get("description"), "age": r.get("age")}
                    for r in data.get("news", {}).get("results", [])
                ]

                return SkillResult.success({
                    "query": query,
                    "web": web_results,
                    "news": news_results,
                    "count": len(web_results),
                })
        except Exception as e:
            return SkillResult.error(f"Brave Search error: {e}")

    def _search_news(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        count = min(context.parameters.get("count", 10), 20)
        freshness = context.parameters.get("freshness")

        headers, err = self._get_headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            params = {"q": query, "count": count}
            if freshness:
                params["freshness"] = freshness

            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/news/search", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

                results = [
                    {"title": r.get("title"), "url": r.get("url"),
                     "description": r.get("description"), "age": r.get("age"),
                     "source": r.get("meta_url", {}).get("hostname")}
                    for r in data.get("results", [])
                ]
                return SkillResult.success(results, count=len(results))
        except Exception as e:
            return SkillResult.error(f"Brave Search error: {e}")


def create_skill() -> BraveSearchSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return BraveSearchSkill(manifest)
