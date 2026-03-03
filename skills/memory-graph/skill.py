"""
memory-graph - Persistent agent memory via knowledge graph

A SkillGuard official skill for maintaining persistent memory across agent
sessions using a JSON-backed knowledge graph of entities and relations.
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
"""

import json
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class MemoryGraphSkill(Skill):
    """Persistent knowledge graph memory skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "create_entities": self._create_entities,
            "create_relations": self._create_relations,
            "add_observations": self._add_observations,
            "search_nodes": self._search_nodes,
            "open_nodes": self._open_nodes,
            "read_graph": self._read_graph,
            "delete_entities": self._delete_entities,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _graph_path(self, context: SkillContext) -> Path:
        memory_dir = context.workspace / ".skillguard" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        return memory_dir / "graph.json"

    def _load_graph(self, context: SkillContext) -> dict:
        path = self._graph_path(context)
        if not path.exists():
            return {"entities": [], "relations": []}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {"entities": [], "relations": []}

    def _save_graph(self, context: SkillContext, graph: dict) -> None:
        path = self._graph_path(context)
        path.write_text(json.dumps(graph, indent=2))

    def _create_entities(self, context: SkillContext) -> SkillResult:
        entities = context.parameters.get("entities", [])
        if not entities:
            return SkillResult.error("Missing required parameter: entities")

        if context.dry_run:
            return SkillResult.success([], dry_run=True, would_create=len(entities))

        try:
            graph = self._load_graph(context)
            existing_names = {e["name"] for e in graph["entities"]}
            created = []

            for entity in entities:
                name = entity.get("name")
                if not name:
                    continue
                if name in existing_names:
                    for e in graph["entities"]:
                        if e["name"] == name:
                            e.setdefault("observations", []).extend(entity.get("observations", []))
                            created.append(e)
                else:
                    new_entity = {
                        "name": name,
                        "entityType": entity.get("type", "unknown"),
                        "observations": entity.get("observations", []),
                    }
                    graph["entities"].append(new_entity)
                    existing_names.add(name)
                    created.append(new_entity)

            self._save_graph(context, graph)
            return SkillResult.success(created, count=len(created))
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _create_relations(self, context: SkillContext) -> SkillResult:
        relations = context.parameters.get("relations", [])
        if not relations:
            return SkillResult.error("Missing required parameter: relations")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            graph = self._load_graph(context)
            entity_names = {e["name"] for e in graph["entities"]}
            created = []

            for rel in relations:
                from_node = rel.get("from")
                to_node = rel.get("to")
                rel_type = rel.get("relationType")
                if not all([from_node, to_node, rel_type]):
                    continue
                if from_node not in entity_names or to_node not in entity_names:
                    continue

                new_rel = {"from": from_node, "to": to_node, "relationType": rel_type}
                existing = [r for r in graph["relations"]
                            if r["from"] == from_node and r["to"] == to_node
                            and r["relationType"] == rel_type]
                if not existing:
                    graph["relations"].append(new_rel)
                    created.append(new_rel)

            self._save_graph(context, graph)
            return SkillResult.success(created, count=len(created))
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _add_observations(self, context: SkillContext) -> SkillResult:
        observations = context.parameters.get("observations", [])
        if not observations:
            return SkillResult.error("Missing required parameter: observations")

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            graph = self._load_graph(context)
            updated = []

            for obs in observations:
                entity_name = obs.get("entityName")
                contents = obs.get("contents", [])
                for entity in graph["entities"]:
                    if entity["name"] == entity_name:
                        entity.setdefault("observations", []).extend(contents)
                        updated.append(entity_name)
                        break

            self._save_graph(context, graph)
            return SkillResult.success(updated, count=len(updated))
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _search_nodes(self, context: SkillContext) -> SkillResult:
        query = context.parameters.get("query")
        if not query:
            return SkillResult.error("Missing required parameter: query")

        try:
            graph = self._load_graph(context)
            query_lower = query.lower()

            matching_entities = [
                e for e in graph["entities"]
                if query_lower in e["name"].lower()
                or any(query_lower in obs.lower() for obs in e.get("observations", []))
            ]

            entity_names = {e["name"] for e in matching_entities}
            matching_relations = [
                r for r in graph["relations"]
                if r["from"] in entity_names or r["to"] in entity_names
            ]

            return SkillResult.success({
                "entities": matching_entities,
                "relations": matching_relations,
            }, count=len(matching_entities))
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _open_nodes(self, context: SkillContext) -> SkillResult:
        names = context.parameters.get("names", [])
        if not names:
            return SkillResult.error("Missing required parameter: names")

        try:
            graph = self._load_graph(context)
            entities = [e for e in graph["entities"] if e["name"] in names]
            entity_names = {e["name"] for e in entities}
            relations = [r for r in graph["relations"]
                         if r["from"] in entity_names and r["to"] in entity_names]
            return SkillResult.success({"entities": entities, "relations": relations})
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _read_graph(self, context: SkillContext) -> SkillResult:
        try:
            graph = self._load_graph(context)
            return SkillResult.success(graph,
                                       entities=len(graph["entities"]),
                                       relations=len(graph["relations"]))
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")

    def _delete_entities(self, context: SkillContext) -> SkillResult:
        entity_names = context.parameters.get("entity_names", [])
        if not entity_names:
            return SkillResult.error("Missing required parameter: entity_names")

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_delete=entity_names)

        try:
            graph = self._load_graph(context)
            names_set = set(entity_names)
            original_count = len(graph["entities"])
            graph["entities"] = [e for e in graph["entities"] if e["name"] not in names_set]
            graph["relations"] = [r for r in graph["relations"]
                                  if r["from"] not in names_set and r["to"] not in names_set]
            deleted = original_count - len(graph["entities"])
            self._save_graph(context, graph)
            return SkillResult.success({"deleted": deleted})
        except Exception as e:
            return SkillResult.error(f"Memory graph error: {e}")


def create_skill() -> MemoryGraphSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return MemoryGraphSkill(manifest)
