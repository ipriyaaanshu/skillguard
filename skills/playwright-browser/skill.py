"""
playwright-browser - Real browser automation via Playwright

A SkillGuard official skill for controlling real Chromium browsers via
accessibility trees. Navigate, click, screenshot, and extract content.
Upstream: https://github.com/microsoft/playwright-mcp
"""

from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class PlaywrightBrowserSkill(Skill):
    """Real browser automation via Playwright."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "navigate": self._navigate,
            "screenshot": self._screenshot,
            "click": self._click,
            "fill_form": self._fill_form,
            "extract_content": self._extract_content,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _navigate(self, context: SkillContext) -> SkillResult:
        url = context.parameters.get("url")
        if not url:
            return SkillResult.error("Missing required parameter: url")

        wait_for = context.parameters.get("wait_for", "load")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_navigate=url)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until=wait_for, timeout=context.timeout_seconds * 1000)
                title = page.title()
                content = page.inner_text("body")[:20000]
                final_url = page.url
                browser.close()
                return SkillResult.success({
                    "title": title,
                    "url": final_url,
                    "content": content,
                })
        except ImportError:
            return SkillResult.error("playwright not installed: pip install playwright && playwright install chromium")
        except Exception as e:
            return SkillResult.error(f"Browser error: {e}")

    def _screenshot(self, context: SkillContext) -> SkillResult:
        import base64
        import tempfile

        url = context.parameters.get("url")
        selector = context.parameters.get("selector")
        full_page = context.parameters.get("full_page", False)

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()

                if url:
                    page.goto(url, wait_until="load", timeout=context.timeout_seconds * 1000)

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name

                if selector:
                    element = page.locator(selector).first
                    element.screenshot(path=tmp_path)
                else:
                    page.screenshot(path=tmp_path, full_page=full_page)

                browser.close()

                with open(tmp_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()

                Path(tmp_path).unlink(missing_ok=True)
                return SkillResult.success({"image_base64": img_b64, "format": "png"})
        except ImportError:
            return SkillResult.error("playwright not installed: pip install playwright && playwright install chromium")
        except Exception as e:
            return SkillResult.error(f"Screenshot error: {e}")

    def _click(self, context: SkillContext) -> SkillResult:
        selector = context.parameters.get("selector")
        if not selector:
            return SkillResult.error("Missing required parameter: selector")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_click=selector)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.locator(selector).first.click(timeout=context.timeout_seconds * 1000)
                title = page.title()
                url = page.url
                browser.close()
                return SkillResult.success({"title": title, "url": url, "clicked": selector})
        except ImportError:
            return SkillResult.error("playwright not installed")
        except Exception as e:
            return SkillResult.error(f"Click error: {e}")

    def _fill_form(self, context: SkillContext) -> SkillResult:
        selector = context.parameters.get("selector")
        value = context.parameters.get("value")
        if not selector or value is None:
            return SkillResult.error("Missing required parameters: selector, value")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_fill=selector)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.locator(selector).first.fill(value, timeout=context.timeout_seconds * 1000)
                browser.close()
                return SkillResult.success({"filled": selector, "value_length": len(str(value))})
        except ImportError:
            return SkillResult.error("playwright not installed")
        except Exception as e:
            return SkillResult.error(f"Fill error: {e}")

    def _extract_content(self, context: SkillContext) -> SkillResult:
        selector = context.parameters.get("selector")
        fmt = context.parameters.get("format", "text")

        if context.dry_run:
            return SkillResult.success("", dry_run=True)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()

                if selector:
                    element = page.locator(selector).first
                    if fmt == "html":
                        content = element.inner_html()
                    else:
                        content = element.inner_text()
                else:
                    if fmt == "html":
                        content = page.content()
                    else:
                        content = page.inner_text("body")

                browser.close()
                return SkillResult.success(content[:50000])
        except ImportError:
            return SkillResult.error("playwright not installed")
        except Exception as e:
            return SkillResult.error(f"Extract error: {e}")


def create_skill() -> PlaywrightBrowserSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return PlaywrightBrowserSkill(manifest)
