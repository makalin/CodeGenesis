"""Code search and exploration tools."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from genesis.vector_db import VectorDatabase
from genesis.config import Config


class CodeSearcher:
    """Advanced code search functionality."""

    def __init__(self, vector_db: VectorDatabase, config: Config):
        """Initialize code searcher."""
        self.vector_db = vector_db
        self.config = config

    def semantic_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using vector database."""
        results = self.vector_db.search(query, n_results=n_results)
        return results

    def grep_search(self, pattern: str, repo_path: Path, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Search for regex pattern in codebase."""
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        matches = []
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if compiled_pattern.search(line):
                            matches.append({
                                "file": str(file_path),
                                "line": line_num,
                                "content": line.strip(),
                                "match": compiled_pattern.search(line).group(),
                            })
            except Exception:
                continue
        
        return matches

    def find_function(self, function_name: str, repo_path: Path, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Find function definitions by name."""
        import ast
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        results = []
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        results.append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node),
                        })
            except Exception:
                continue
        
        return results

    def find_class(self, class_name: str, repo_path: Path, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Find class definitions by name."""
        import ast
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        results = []
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        results.append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "name": node.name,
                            "bases": [ast.unparse(b) if hasattr(ast, "unparse") else str(b) for b in node.bases],
                            "methods": methods,
                            "docstring": ast.get_docstring(node),
                        })
            except Exception:
                continue
        
        return results

    def find_imports(self, module_name: str, repo_path: Path, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Find all files that import a specific module."""
        import ast
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        results = []
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith(module_name):
                                results.append({
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "import": alias.name,
                                    "type": "import",
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith(module_name):
                            results.append({
                                "file": str(file_path),
                                "line": node.lineno,
                                "import": node.module,
                                "type": "from_import",
                            })
            except Exception:
                continue
        
        return results

    def find_usage(self, symbol_name: str, repo_path: Path, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Find all usages of a symbol (function, class, variable)."""
        import ast
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        results = []
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == symbol_name:
                        results.append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "symbol": symbol_name,
                            "context": self._get_context(content, node.lineno),
                        })
            except Exception:
                continue
        
        return results

    def _get_context(self, content: str, line_num: int, context_lines: int = 3) -> str:
        """Get context around a line."""
        lines = content.split("\n")
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return "\n".join(lines[start:end])

    def find_similar_code(self, file_path: Path, repo_path: Path, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar code blocks using vector similarity."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Search for similar code
            results = self.vector_db.search(content, n_results=10)
            
            similar = []
            for result in results:
                if result.get("distance", 1.0) < (1 - threshold):
                    similar.append({
                        "file": result.get("metadata", {}).get("file_path", "unknown"),
                        "similarity": 1 - result.get("distance", 1.0),
                        "content": result.get("document", "")[:200],
                    })
            
            return similar
        except Exception:
            return []

