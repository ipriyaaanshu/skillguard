"""
git-local - Local git operations for AI agents

A SkillGuard official skill for interacting with local git repositories.
Status, diff, log, commit, branch management, and blame.
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/git
"""

from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class GitLocalSkill(Skill):
    """Local git operations skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "status": self._status,
            "diff": self._diff,
            "log": self._log,
            "commit": self._commit,
            "branch_list": self._branch_list,
            "blame": self._blame,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _get_repo(self, context: SkillContext):
        try:
            import git
        except ImportError:
            return None, SkillResult.error("gitpython not installed: pip install gitpython")

        repo_path = context.parameters.get("repo_path", str(context.workspace))

        resolved = (context.workspace / repo_path).resolve()
        if not self._is_within_workspace(resolved, context.workspace):
            return None, SkillResult.denied("repo_path is outside workspace")

        try:
            repo = git.Repo(resolved, search_parent_directories=True)
            return repo, None
        except git.InvalidGitRepositoryError:
            return None, SkillResult.error(f"Not a git repository: {repo_path}")
        except Exception as e:
            return None, SkillResult.error(f"Git error: {e}")

    def _is_within_workspace(self, path: Path, workspace: Path) -> bool:
        try:
            path.relative_to(workspace.resolve())
            return True
        except ValueError:
            return False

    def _status(self, context: SkillContext) -> SkillResult:
        repo, err = self._get_repo(context)
        if err:
            return err

        try:
            staged = [item.a_path for item in repo.index.diff("HEAD")]
            unstaged = [item.a_path for item in repo.index.diff(None)]
            untracked = repo.untracked_files
            return SkillResult.success({
                "branch": repo.active_branch.name,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "is_dirty": repo.is_dirty(),
            })
        except Exception as e:
            return SkillResult.error(f"Git status error: {e}")

    def _diff(self, context: SkillContext) -> SkillResult:
        repo, err = self._get_repo(context)
        if err:
            return err

        staged = context.parameters.get("staged", False)
        file_path = context.parameters.get("file_path")

        try:
            if staged:
                diff = repo.git.diff("--staged", file_path or ())
            else:
                diff = repo.git.diff(file_path or ())
            return SkillResult.success(diff, lines=diff.count("\n"))
        except Exception as e:
            return SkillResult.error(f"Git diff error: {e}")

    def _log(self, context: SkillContext) -> SkillResult:
        repo, err = self._get_repo(context)
        if err:
            return err

        n = min(context.parameters.get("n", 20), 100)
        branch = context.parameters.get("branch")

        try:
            ref = branch or repo.active_branch.name
            commits = list(repo.iter_commits(ref, max_count=n))
            return SkillResult.success([
                {
                    "hash": c.hexsha[:12],
                    "author": str(c.author),
                    "date": c.authored_datetime.isoformat(),
                    "message": c.message.strip(),
                }
                for c in commits
            ], count=len(commits))
        except Exception as e:
            return SkillResult.error(f"Git log error: {e}")

    def _commit(self, context: SkillContext) -> SkillResult:
        message = context.parameters.get("message")
        if not message:
            return SkillResult.error("Missing required parameter: message")

        repo, err = self._get_repo(context)
        if err:
            return err

        files = context.parameters.get("files", [])

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_commit=message)

        try:
            if files:
                repo.index.add(files)
            else:
                repo.git.add("-u")

            commit = repo.index.commit(message)
            return SkillResult.success({
                "hash": commit.hexsha[:12],
                "message": commit.message.strip(),
            })
        except Exception as e:
            return SkillResult.error(f"Git commit error: {e}")

    def _branch_list(self, context: SkillContext) -> SkillResult:
        repo, err = self._get_repo(context)
        if err:
            return err

        include_all = context.parameters.get("all", False)

        try:
            current = repo.active_branch.name
            branches = [{"name": b.name, "current": b.name == current}
                        for b in repo.branches]

            if include_all:
                remote_branches = [{"name": ref.name, "current": False, "remote": True}
                                   for ref in repo.remote().refs]
                branches.extend(remote_branches)

            return SkillResult.success(branches, count=len(branches))
        except Exception as e:
            return SkillResult.error(f"Git branch error: {e}")

    def _blame(self, context: SkillContext) -> SkillResult:
        file_path = context.parameters.get("file_path")
        if not file_path:
            return SkillResult.error("Missing required parameter: file_path")

        repo, err = self._get_repo(context)
        if err:
            return err

        try:
            blame = repo.blame("HEAD", file_path)
            lines = []
            line_num = 1
            for commit, file_lines in blame:
                for line in file_lines:
                    lines.append({
                        "line": line_num,
                        "hash": commit.hexsha[:12],
                        "author": str(commit.author),
                        "date": commit.authored_datetime.isoformat(),
                        "content": line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line,
                    })
                    line_num += 1
            return SkillResult.success(lines, count=len(lines))
        except Exception as e:
            return SkillResult.error(f"Git blame error: {e}")


def create_skill() -> GitLocalSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return GitLocalSkill(manifest)
