"""SkillGuard client that delegates all operations to the Rust CLI binary."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    """Result from a skill execution."""

    status: str
    data: Any = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillGuardError(Exception):
    """Error from SkillGuard CLI."""

    pass


class SkillGuardClient:
    """Client for interacting with SkillGuard skills via the Rust CLI.

    All operations are delegated to the `skillguard` CLI binary,
    ensuring all security enforcement (sandbox, signing, verification)
    is handled by the Rust implementation.
    """

    def __init__(self, cli_path: str | None = None):
        """Initialize the client.

        Args:
            cli_path: Path to the skillguard binary. If None, searches PATH.
        """
        if cli_path:
            self._cli = cli_path
        else:
            found = shutil.which("skillguard")
            if not found:
                raise SkillGuardError(
                    "skillguard CLI not found in PATH. "
                    "Install from https://github.com/ipriyaaanshu/agents/releases"
                )
            self._cli = found

    def _run_cli(self, *args: str) -> dict[str, Any]:
        """Run a CLI command and return parsed JSON output."""
        cmd = [self._cli, "--output-json", *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired as e:
            raise SkillGuardError("CLI command timed out") from e
        except FileNotFoundError as e:
            raise SkillGuardError(f"CLI binary not found at {self._cli}") from e

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise SkillGuardError(f"CLI error (exit {result.returncode}): {stderr}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw_output": result.stdout.strip()}

    def run(
        self,
        skill: str,
        action: str,
        params: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> SkillResult:
        """Execute a skill action in the sandboxed environment.

        Args:
            skill: Skill name or path.
            action: Action to execute.
            params: Parameters as a dictionary.
            dry_run: If True, show what would happen without executing.

        Returns:
            SkillResult with execution outcome.
        """
        args = ["run", skill, "--action", action]
        if params:
            args.extend(["--params", json.dumps(params)])
        if dry_run:
            args.append("--dry-run")

        result = self._run_cli(*args)
        return SkillResult(
            status=result.get("status", "error"),
            data=result.get("data"),
            error_message=result.get("error_message"),
            metadata=result.get("metadata", {}),
        )

    def info(self, skill: str) -> dict[str, Any]:
        """Get information about a skill."""
        return self._run_cli("info", skill)

    def list_skills(self, installed: bool = True) -> list[dict[str, Any]]:
        """List available skills."""
        args = ["list"]
        if installed:
            args.append("--installed")
        result = self._run_cli(*args)
        return result if isinstance(result, list) else [result]

    def install(self, skill: str, force: bool = False) -> dict[str, Any]:
        """Install a skill from the registry."""
        args = ["install", skill]
        if force:
            args.append("--force")
        return self._run_cli(*args)

    def audit(self, path: str = ".") -> list[dict[str, Any]]:
        """Audit a skill for security issues."""
        result = self._run_cli("audit", path)
        return result if isinstance(result, list) else [result]

    def build(self, path: str = ".", sign: bool = False) -> dict[str, Any]:
        """Build a skill package."""
        args = ["build", path]
        if sign:
            args.append("--sign")
        return self._run_cli(*args)

    def verify(self, skill: str, strict: bool = False) -> dict[str, Any]:
        """Verify a skill's signatures and provenance."""
        args = ["verify", skill]
        if strict:
            args.append("--strict")
        return self._run_cli(*args)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the registry."""
        result = self._run_cli("search", query, "--limit", str(limit))
        return result if isinstance(result, list) else [result]

    def wrap(self, skill_dir: str) -> dict[str, Any]:
        """Wrap an Anthropic Agent Skill with a security sidecar."""
        return self._run_cli("wrap", skill_dir)

    def export(self, path: str = ".", format: str = "anthropic") -> dict[str, Any]:
        """Export a skill in another format."""
        return self._run_cli("export", "--format", format, path)
