"""
context7-docs - Fetch current library documentation at query time

A SkillGuard official skill that fetches up-to-date, version-pinned library
documentation to eliminate hallucinated APIs from stale training data.
Upstream: https://github.com/upstash/context7
"""

from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class Context7DocsSkill(Skill):
    """Context7 live documentation fetcher skill."""

    _BASE_URL = "https://context7.com/api"

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "resolve_library": self._resolve_library,
            "get_docs": self._get_docs,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _resolve_library(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        library_name = context.parameters.get("library_name")
        if not library_name:
            return SkillResult.error("Missing required parameter: library_name")

        if context.dry_run:
            return SkillResult.success([], dry_run=True, would_resolve=library_name)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.get(f"{self._BASE_URL}/v1/search",
                                  params={"query": library_name})
                resp.raise_for_status()
                data = resp.json()
                results = [
                    {"id": lib.get("id"), "name": lib.get("name"),
                     "description": lib.get("description"),
                     "version": lib.get("version")}
                    for lib in data.get("results", [])[:10]
                ]
                return SkillResult.success(results, count=len(results))
        except Exception as e:
            return SkillResult.error(f"Context7 API error: {e}")

    def _get_docs(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        library_id = context.parameters.get("library_id")
        if not library_id:
            return SkillResult.error("Missing required parameter: library_id")

        topic = context.parameters.get("topic", "")
        tokens = min(context.parameters.get("tokens", 5000), 20000)

        if context.dry_run:
            return SkillResult.success("", dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                params = {"tokens": tokens}
                if topic:
                    params["topic"] = topic

                resp = client.get(f"{self._BASE_URL}/v1{library_id}", params=params)
                resp.raise_for_status()
                data = resp.json()
                docs = data.get("content", "") or data.get("text", "") or str(data)
                return SkillResult.success(docs, chars=len(docs))
        except Exception as e:
            return SkillResult.error(f"Context7 API error: {e}")


def create_skill() -> Context7DocsSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return Context7DocsSkill(manifest)
