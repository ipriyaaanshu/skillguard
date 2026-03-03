"""
docker-mcp - Docker container management for AI agents

A SkillGuard official skill for managing Docker containers, images,
and logs via the Docker SDK.
Upstream: https://github.com/docker/mcp-server
"""

from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class DockerMCPSkill(Skill):
    """Docker container management skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "list_containers": self._list_containers,
            "get_logs": self._get_logs,
            "run_container": self._run_container,
            "stop_container": self._stop_container,
            "list_images": self._list_images,
            "inspect_container": self._inspect_container,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _client(self):
        try:
            import docker
            return docker.from_env(), None
        except ImportError:
            return None, SkillResult.error("docker SDK not installed: pip install docker")
        except Exception as e:
            return None, SkillResult.error(f"Docker connection error: {e}")

    def _list_containers(self, context: SkillContext) -> SkillResult:
        client, err = self._client()
        if err:
            return err

        include_all = context.parameters.get("all", False)
        filters = context.parameters.get("filters", {})

        try:
            containers = client.containers.list(all=include_all, filters=filters)
            result = [{
                "id": c.short_id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                "status": c.status,
                "ports": c.ports,
            } for c in containers]
            return SkillResult.success(result, count=len(result))
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")

    def _get_logs(self, context: SkillContext) -> SkillResult:
        container_name = context.parameters.get("container")
        if not container_name:
            return SkillResult.error("Missing required parameter: container")

        tail = context.parameters.get("tail", 100)
        since = context.parameters.get("since")

        client, err = self._client()
        if err:
            return err

        try:
            container = client.containers.get(container_name)
            kwargs = {"tail": tail, "timestamps": True}
            if since:
                kwargs["since"] = since
            logs = container.logs(**kwargs)
            if isinstance(logs, bytes):
                logs = logs.decode("utf-8", errors="replace")
            return SkillResult.success(logs)
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")

    def _run_container(self, context: SkillContext) -> SkillResult:
        image = context.parameters.get("image")
        if not image:
            return SkillResult.error("Missing required parameter: image")

        command = context.parameters.get("command")
        environment = context.parameters.get("environment", {})
        ports = context.parameters.get("ports", {})
        detach = context.parameters.get("detach", True)

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_run=image)

        client, err = self._client()
        if err:
            return err

        try:
            container = client.containers.run(
                image,
                command=command,
                environment=environment,
                ports=ports,
                detach=detach,
            )
            if detach:
                return SkillResult.success({
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                })
            else:
                output = container.decode("utf-8", errors="replace") if isinstance(container, bytes) else str(container)
                return SkillResult.success({"output": output})
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")

    def _stop_container(self, context: SkillContext) -> SkillResult:
        container_name = context.parameters.get("container")
        if not container_name:
            return SkillResult.error("Missing required parameter: container")

        timeout = context.parameters.get("timeout", 10)

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_stop=container_name)

        client, err = self._client()
        if err:
            return err

        try:
            container = client.containers.get(container_name)
            container.stop(timeout=timeout)
            return SkillResult.success({"stopped": container_name, "id": container.short_id})
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")

    def _list_images(self, context: SkillContext) -> SkillResult:
        filters = context.parameters.get("filters", {})

        client, err = self._client()
        if err:
            return err

        try:
            images = client.images.list(filters=filters)
            result = [{
                "id": img.short_id,
                "tags": img.tags,
                "size_mb": round(img.attrs.get("Size", 0) / 1024 / 1024, 1),
                "created": img.attrs.get("Created"),
            } for img in images]
            return SkillResult.success(result, count=len(result))
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")

    def _inspect_container(self, context: SkillContext) -> SkillResult:
        container_name = context.parameters.get("container")
        if not container_name:
            return SkillResult.error("Missing required parameter: container")

        client, err = self._client()
        if err:
            return err

        try:
            container = client.containers.get(container_name)
            attrs = container.attrs
            return SkillResult.success({
                "id": attrs["Id"][:12],
                "name": attrs["Name"].lstrip("/"),
                "image": attrs["Config"]["Image"],
                "status": attrs["State"]["Status"],
                "started_at": attrs["State"].get("StartedAt"),
                "ip_address": attrs.get("NetworkSettings", {}).get("IPAddress"),
                "ports": attrs.get("NetworkSettings", {}).get("Ports", {}),
                "env": attrs["Config"].get("Env", []),
                "mounts": [{"source": m["Source"], "dest": m["Destination"]}
                           for m in attrs.get("Mounts", [])],
            })
        except Exception as e:
            return SkillResult.error(f"Docker error: {e}")


def create_skill() -> DockerMCPSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return DockerMCPSkill(manifest)
