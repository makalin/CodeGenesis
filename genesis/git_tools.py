"""Git integration tools."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import json
from datetime import datetime

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class GitIntegration:
    """Git integration for Code Genesis."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize git integration."""
        if not GIT_AVAILABLE:
            raise ImportError("GitPython not available. Install with: pip install gitpython")
        
        if repo_path is None:
            repo_path = Path.cwd()
        
        try:
            self.repo = Repo(repo_path)
        except Exception:
            raise ValueError(f"Not a git repository: {repo_path}")

    def create_feature_branch(self, branch_name: str) -> bool:
        """Create a new feature branch for generated code."""
        try:
            if self.repo.is_dirty():
                raise ValueError("Repository has uncommitted changes. Commit or stash first.")
            
            # Create and checkout branch
            branch = self.repo.create_head(branch_name)
            branch.checkout()
            return True
        except Exception as e:
            print(f"Error creating branch: {e}")
            return False

    def commit_generated_code(self, files: List[Path], message: str, author: Optional[str] = None) -> bool:
        """Commit generated code files."""
        try:
            # Stage files
            for file_path in files:
                if file_path.exists():
                    self.repo.index.add([str(file_path)])
            
            # Commit
            commit = self.repo.index.commit(
                message,
                author=author or self.repo.config_reader().get_value("user", "name", "Code Genesis"),
            )
            
            return True
        except Exception as e:
            print(f"Error committing: {e}")
            return False

    def create_pull_request_info(self, branch_name: str, title: str, description: str) -> Dict[str, Any]:
        """Create pull request information."""
        return {
            "branch": branch_name,
            "title": title,
            "description": description,
            "files_changed": [str(f) for f in self.repo.index.diff("HEAD")],
            "created_at": datetime.now().isoformat(),
        }

    def get_diff(self, file_path: Optional[Path] = None) -> str:
        """Get git diff for file or all changes."""
        try:
            if file_path:
                return self.repo.git.diff(str(file_path))
            else:
                return self.repo.git.diff()
        except Exception as e:
            return f"Error getting diff: {e}"

    def get_file_history(self, file_path: Path, limit: int = 10) -> List[Dict[str, Any]]:
        """Get commit history for a file."""
        try:
            commits = list(self.repo.iter_commits(paths=str(file_path), max_count=limit))
            
            history = []
            for commit in commits:
                history.append({
                    "hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                })
            
            return history
        except Exception as e:
            return [{"error": str(e)}]

    def stash_changes(self) -> bool:
        """Stash current changes."""
        try:
            self.repo.git.stash()
            return True
        except Exception as e:
            print(f"Error stashing: {e}")
            return False

    def restore_stash(self) -> bool:
        """Restore stashed changes."""
        try:
            self.repo.git.stash("pop")
            return True
        except Exception as e:
            print(f"Error restoring stash: {e}")
            return False


class CodeReviewGenerator:
    """Generate code reviews using LLM."""

    def __init__(self, config):
        """Initialize code review generator."""
        from genesis.llm_client import create_llm_client
        self.config = config
        self.llm_client = create_llm_client(config)

    def review_file(self, file_path: Path) -> Dict[str, Any]:
        """Generate code review for a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            system_prompt = """You are an expert code reviewer. Review the code and provide:
1. Overall assessment
2. Potential bugs or issues
3. Performance concerns
4. Security issues
5. Code quality suggestions
6. Best practices recommendations

Be constructive and specific."""
            
            user_prompt = f"""Review this code file:

{content}

Provide a comprehensive code review."""
            
            review = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
            
            return {
                "file": str(file_path),
                "review": review,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def review_diff(self, diff: str) -> Dict[str, Any]:
        """Review a git diff."""
        system_prompt = """You are an expert code reviewer. Review the git diff and provide:
1. Overall assessment of changes
2. Potential issues introduced
3. Suggestions for improvement
4. Missing tests or documentation"""
        
        user_prompt = f"""Review this git diff:

{diff}

Provide a comprehensive review of the changes."""
        
        review = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        return {
            "review": review,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_review_summary(self, reviews: List[Dict[str, Any]]) -> str:
        """Generate summary of multiple reviews."""
        system_prompt = "Summarize code reviews into a concise report."
        
        reviews_text = "\n\n".join([f"File: {r.get('file', 'unknown')}\n{r.get('review', '')}" for r in reviews])
        
        user_prompt = f"""Summarize these code reviews:

{reviews_text}

Create a concise summary report."""
        
        summary = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        return summary

