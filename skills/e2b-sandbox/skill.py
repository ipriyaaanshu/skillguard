"""
e2b-sandbox - Safe cloud code execution in isolated microVMs

A SkillGuard official skill for running arbitrary code in E2B cloud sandboxes.
All execution happens in isolated microVMs — no local system access.
Upstream: https://github.com/e2b-dev/mcp-server
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class E2BSandboxSkill(Skill):
    """E2B cloud sandbox code execution skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "run_code": self._run_code,
            "run_shell": self._run_shell,
            "run_javascript": self._run_javascript,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _get_api_key(self, context: SkillContext):
        key = os.environ.get("E2B_API_KEY") or context.secrets.get("E2B_API_KEY")
        if not key:
            return None, SkillResult.error("E2B_API_KEY not set")
        return key, None

    def _run_code(self, context: SkillContext) -> SkillResult:
        code = context.parameters.get("code")
        if not code:
            return SkillResult.error("Missing required parameter: code")

        timeout = min(context.parameters.get("timeout", 30), 300)
        packages = context.parameters.get("packages", [])

        api_key, err = self._get_api_key(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True,
                                       would_execute=code[:100] + ("..." if len(code) > 100 else ""))

        try:
            from e2b_code_interpreter import Sandbox
            with Sandbox(api_key=api_key, timeout=timeout) as sbx:
                if packages:
                    install_result = sbx.commands.run(
                        f"pip install -q {' '.join(packages)}", timeout=60
                    )
                    if install_result.exit_code != 0:
                        return SkillResult.error(f"Package install failed: {install_result.stderr}")

                execution = sbx.run_code(code)
                return SkillResult.success({
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "results": [str(r) for r in (execution.results or [])],
                    "error": str(execution.error) if execution.error else None,
                })
        except ImportError:
            return SkillResult.error("e2b-code-interpreter not installed: pip install e2b-code-interpreter")
        except Exception as e:
            return SkillResult.error(f"E2B execution error: {e}")

    def _run_shell(self, context: SkillContext) -> SkillResult:
        command = context.parameters.get("command")
        if not command:
            return SkillResult.error("Missing required parameter: command")

        timeout = min(context.parameters.get("timeout", 30), 300)

        api_key, err = self._get_api_key(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_run=command)

        try:
            from e2b_code_interpreter import Sandbox
            with Sandbox(api_key=api_key, timeout=timeout) as sbx:
                result = sbx.commands.run(command, timeout=timeout)
                return SkillResult.success({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                })
        except ImportError:
            return SkillResult.error("e2b-code-interpreter not installed: pip install e2b-code-interpreter")
        except Exception as e:
            return SkillResult.error(f"E2B execution error: {e}")

    def _run_javascript(self, context: SkillContext) -> SkillResult:
        code = context.parameters.get("code")
        if not code:
            return SkillResult.error("Missing required parameter: code")

        timeout = min(context.parameters.get("timeout", 30), 300)
        packages = context.parameters.get("packages", [])

        api_key, err = self._get_api_key(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            from e2b_code_interpreter import Sandbox
            with Sandbox(api_key=api_key, timeout=timeout) as sbx:
                if packages:
                    install_result = sbx.commands.run(
                        f"npm install -q {' '.join(packages)}", timeout=60
                    )
                    if install_result.exit_code != 0:
                        return SkillResult.error(f"npm install failed: {install_result.stderr}")

                execution = sbx.run_code(code, language="javascript")
                return SkillResult.success({
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "results": [str(r) for r in (execution.results or [])],
                    "error": str(execution.error) if execution.error else None,
                })
        except ImportError:
            return SkillResult.error("e2b-code-interpreter not installed: pip install e2b-code-interpreter")
        except Exception as e:
            return SkillResult.error(f"E2B execution error: {e}")


def create_skill() -> E2BSandboxSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return E2BSandboxSkill(manifest)
