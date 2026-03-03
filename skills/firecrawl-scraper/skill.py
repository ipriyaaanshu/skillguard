"""
firecrawl-scraper - Convert any URL into clean LLM-ready Markdown

A SkillGuard official skill for scraping, crawling, and extracting structured
data from websites via the Firecrawl API. Strips ads, nav, and markup.
Upstream: https://github.com/mendableai/firecrawl-mcp-server
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class FirecrawlScraperSkill(Skill):
    """Firecrawl web scraping and crawling skill."""

    _BASE_URL = "https://api.firecrawl.dev/v1"

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "scrape": self._scrape,
            "crawl": self._crawl,
            "map": self._map,
            "extract": self._extract,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _headers(self, context: SkillContext):
        api_key = os.environ.get("FIRECRAWL_API_KEY") or context.secrets.get("FIRECRAWL_API_KEY")
        if not api_key:
            return None, SkillResult.error("FIRECRAWL_API_KEY not set")
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, None

    def _scrape(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        url = context.parameters.get("url")
        if not url:
            return SkillResult.error("Missing required parameter: url")

        include_html = context.parameters.get("include_html", False)
        only_main = context.parameters.get("only_main_content", True)

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_scrape=url)

        try:
            formats = ["markdown"]
            if include_html:
                formats.append("html")

            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.post(f"{self._BASE_URL}/scrape", headers=headers, json={
                    "url": url,
                    "formats": formats,
                    "onlyMainContent": only_main,
                })
                resp.raise_for_status()
                data = resp.json()
                result = data.get("data", {})
                return SkillResult.success({
                    "markdown": result.get("markdown", ""),
                    "html": result.get("html") if include_html else None,
                    "metadata": result.get("metadata", {}),
                    "url": url,
                })
        except Exception as e:
            return SkillResult.error(f"Firecrawl error: {e}")

    def _crawl(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
            import time
        except ImportError:
            return SkillResult.error("httpx not installed")

        url = context.parameters.get("url")
        if not url:
            return SkillResult.error("Missing required parameter: url")

        limit = min(context.parameters.get("limit", 10), 100)
        include_paths = context.parameters.get("include_paths", [])
        exclude_paths = context.parameters.get("exclude_paths", [])

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True, would_crawl=url)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                payload = {"url": url, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}}
                if include_paths:
                    payload["includePaths"] = include_paths
                if exclude_paths:
                    payload["excludePaths"] = exclude_paths

                resp = client.post(f"{self._BASE_URL}/crawl", headers=headers, json=payload)
                resp.raise_for_status()
                job = resp.json()
                job_id = job.get("id")
                if not job_id:
                    return SkillResult.error("No job ID returned from crawl")

                for _ in range(60):
                    time.sleep(2)
                    status_resp = client.get(f"{self._BASE_URL}/crawl/{job_id}", headers=headers)
                    status_resp.raise_for_status()
                    status_data = status_resp.json()
                    if status_data.get("status") == "completed":
                        pages = [{"url": p.get("metadata", {}).get("sourceURL"),
                                  "markdown": p.get("markdown", "")}
                                 for p in status_data.get("data", [])]
                        return SkillResult.success(pages, count=len(pages))
                    if status_data.get("status") == "failed":
                        return SkillResult.error(f"Crawl failed: {status_data.get('error')}")

                return SkillResult.timeout(120)
        except Exception as e:
            return SkillResult.error(f"Firecrawl error: {e}")

    def _map(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        url = context.parameters.get("url")
        if not url:
            return SkillResult.error("Missing required parameter: url")

        limit = min(context.parameters.get("limit", 100), 5000)

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.post(f"{self._BASE_URL}/map", headers=headers,
                                   json={"url": url, "limit": limit})
                resp.raise_for_status()
                data = resp.json()
                links = data.get("links", [])
                return SkillResult.success(links[:limit], count=len(links))
        except Exception as e:
            return SkillResult.error(f"Firecrawl error: {e}")

    def _extract(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        url = context.parameters.get("url")
        if not url:
            return SkillResult.error("Missing required parameter: url")

        schema = context.parameters.get("schema")
        prompt = context.parameters.get("prompt")

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            payload = {"url": url, "formats": ["extract"]}
            extract_opts = {}
            if schema:
                extract_opts["schema"] = schema
            if prompt:
                extract_opts["prompt"] = prompt
            if extract_opts:
                payload["extract"] = extract_opts

            with httpx.Client(timeout=context.timeout_seconds) as client:
                resp = client.post(f"{self._BASE_URL}/scrape", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                result = data.get("data", {})
                return SkillResult.success(result.get("extract", result))
        except Exception as e:
            return SkillResult.error(f"Firecrawl error: {e}")


def create_skill() -> FirecrawlScraperSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return FirecrawlScraperSkill(manifest)
