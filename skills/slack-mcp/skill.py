"""
slack-mcp - Slack workspace integration for AI agents

A SkillGuard official skill for reading messages, posting to channels,
and searching Slack workspaces via the Slack Web API.
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/slack
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class SlackMCPSkill(Skill):
    """Slack workspace integration skill."""

    _BASE_URL = "https://slack.com/api"

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "list_channels": self._list_channels,
            "get_channel_history": self._get_channel_history,
            "post_message": self._post_message,
            "search_messages": self._search_messages,
            "get_user_info": self._get_user_info,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _headers(self, context: SkillContext):
        token = (os.environ.get("SLACK_BOT_TOKEN") or
                 context.secrets.get("SLACK_BOT_TOKEN"))
        if not token:
            return None, SkillResult.error("SLACK_BOT_TOKEN not set")
        return {"Authorization": f"Bearer {token}",
                "Content-Type": "application/json"}, None

    def _api_call(self, client, method: str, **kwargs):
        import httpx
        resp = client.post(f"{self._BASE_URL}/{method}", **kwargs)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(f"Slack API error: {data.get('error', 'unknown')}")
        return data

    def _list_channels(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        headers, err = self._headers(context)
        if err:
            return err

        exclude_archived = context.parameters.get("exclude_archived", True)
        types = context.parameters.get("types", "public_channel")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                data = self._api_call(client, "conversations.list",
                                      json={"exclude_archived": exclude_archived,
                                            "types": types, "limit": 200},
                                      headers=headers)
                channels = [{"id": c["id"], "name": c["name"],
                             "topic": c.get("topic", {}).get("value", ""),
                             "member_count": c.get("num_members", 0)}
                            for c in data.get("channels", [])]
                return SkillResult.success(channels, count=len(channels))
        except Exception as e:
            return SkillResult.error(f"Slack error: {e}")

    def _get_channel_history(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        channel = context.parameters.get("channel")
        if not channel:
            return SkillResult.error("Missing required parameter: channel")

        limit = min(context.parameters.get("limit", 50), 200)

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                data = self._api_call(client, "conversations.history",
                                      json={"channel": channel, "limit": limit},
                                      headers=headers)
                messages = [{"user": m.get("user"), "text": m.get("text", ""),
                             "ts": m.get("ts"), "thread_ts": m.get("thread_ts")}
                            for m in data.get("messages", [])]
                return SkillResult.success(messages, count=len(messages))
        except Exception as e:
            return SkillResult.error(f"Slack error: {e}")

    def _post_message(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        channel = context.parameters.get("channel")
        text = context.parameters.get("text")
        if not channel or not text:
            return SkillResult.error("Missing required parameters: channel, text")

        thread_ts = context.parameters.get("thread_ts")

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_post_to=channel)

        try:
            payload = {"channel": channel, "text": text}
            if thread_ts:
                payload["thread_ts"] = thread_ts

            with httpx.Client(timeout=context.timeout_seconds) as client:
                data = self._api_call(client, "chat.postMessage",
                                      json=payload, headers=headers)
                return SkillResult.success({
                    "ts": data.get("ts"),
                    "channel": data.get("channel"),
                })
        except Exception as e:
            return SkillResult.error(f"Slack error: {e}")

    def _search_messages(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        count = min(context.parameters.get("count", 20), 100)

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                data = self._api_call(client, "search.messages",
                                      json={"query": query, "count": count},
                                      headers=headers)
                matches = data.get("messages", {}).get("matches", [])
                results = [{"text": m.get("text"), "user": m.get("username"),
                            "channel": m.get("channel", {}).get("name"),
                            "ts": m.get("ts"), "permalink": m.get("permalink")}
                           for m in matches]
                return SkillResult.success(results, count=len(results))
        except Exception as e:
            return SkillResult.error(f"Slack error: {e}")

    def _get_user_info(self, context: SkillContext) -> SkillResult:
        try:
            import httpx
        except ImportError:
            return SkillResult.error("httpx not installed")

        user = context.parameters.get("user")
        if not user:
            return SkillResult.error("Missing required parameter: user")

        headers, err = self._headers(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                data = self._api_call(client, "users.info",
                                      json={"user": user}, headers=headers)
                u = data.get("user", {})
                profile = u.get("profile", {})
                return SkillResult.success({
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "real_name": profile.get("real_name"),
                    "email": profile.get("email"),
                    "title": profile.get("title"),
                    "status": profile.get("status_text"),
                })
        except Exception as e:
            return SkillResult.error(f"Slack error: {e}")


def create_skill() -> SlackMCPSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return SlackMCPSkill(manifest)
