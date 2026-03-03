"""LangChain adapter for SkillGuard skills."""

from __future__ import annotations

import json
from typing import Any

from skillguard.client import SkillGuardClient


def as_tool(
    client: SkillGuardClient,
    skill: str,
    action: str,
    name: str | None = None,
    description: str | None = None,
) -> Any:
    """Create a LangChain Tool from a SkillGuard skill action.

    Args:
        client: SkillGuard client instance.
        skill: Skill name or path.
        action: Action name.
        name: Override tool name (defaults to "{skill}.{action}").
        description: Override description.

    Returns:
        A LangChain Tool instance.

    Raises:
        ImportError: If langchain is not installed.
    """
    try:
        from langchain_core.tools import Tool
    except ImportError as e:
        raise ImportError(
            "langchain-core is required for LangChain integration. "
            "Install with: pip install langchain-core"
        ) from e

    tool_name = name or f"{skill}.{action}"

    # Get description from manifest if not provided
    if not description:
        try:
            info = client.info(skill)
            for act in info.get("actions", []):
                if act.get("name") == action:
                    description = act.get("description", f"Execute {action} on {skill}")
                    break
        except Exception:
            description = f"Execute {action} on {skill}"

    def _run(params_str: str) -> str:
        try:
            params = json.loads(params_str)
        except json.JSONDecodeError:
            params = {"input": params_str}

        result = client.run(skill, action, params)
        if result.status == "success":
            return json.dumps(result.data) if result.data else "Success"
        else:
            return f"Error: {result.error_message}"

    return Tool(
        name=tool_name,
        description=description or "",
        func=_run,
    )
