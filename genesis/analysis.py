"""Code analysis tools for complexity, metrics, and dependency analysis."""

import ast
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter
import json


class CodeAnalyzer:
    """Analyzes code complexity, metrics, and dependencies."""

    def __init__(self):
        """Initialize code analyzer."""
        self.complexity_cache: Dict[str, int] = {}

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            return {
                "file_path": str(file_path),
                "lines_of_code": len(content.split("\n")),
                "lines_of_code_excluding_comments": self._count_code_lines(content),
                "cyclomatic_complexity": self._calculate_cyclomatic_complexity(tree),
                "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "import_count": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
                "average_function_length": self._average_function_length(tree),
                "max_nesting_depth": self._max_nesting_depth(tree),
                "dependencies": self._extract_dependencies(tree),
            }
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
            }

    def analyze_repository(self, repo_path: Path, ignore_patterns: List[str] = None) -> Dict[str, Any]:
        """Analyze entire repository."""
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = []
        
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        file_analyses = []
        total_loc = 0
        total_complexity = 0
        all_dependencies = set()
        
        for file_path in python_files:
            analysis = self.analyze_file(file_path)
            if "error" not in analysis:
                file_analyses.append(analysis)
                total_loc += analysis.get("lines_of_code", 0)
                total_complexity += analysis.get("cyclomatic_complexity", 0)
                all_dependencies.update(analysis.get("dependencies", []))
        
        return {
            "total_files": len(file_analyses),
            "total_lines_of_code": total_loc,
            "average_complexity": total_complexity / len(file_analyses) if file_analyses else 0,
            "total_complexity": total_complexity,
            "dependencies": sorted(list(all_dependencies)),
            "files": file_analyses,
            "most_complex_files": sorted(
                file_analyses,
                key=lambda x: x.get("cyclomatic_complexity", 0),
                reverse=True
            )[:10],
        }

    def _count_code_lines(self, content: str) -> int:
        """Count lines of code excluding comments and blank lines."""
        lines = content.split("\n")
        code_lines = 0
        in_multiline_string = False
        quote_char = None
        
        for line in lines:
            stripped = line.strip()
            
            # Skip blank lines
            if not stripped:
                continue
            
            # Handle multiline strings
            if '"""' in stripped or "'''" in stripped:
                in_multiline_string = not in_multiline_string
            
            if in_multiline_string:
                continue
            
            # Skip comment-only lines
            if stripped.startswith("#"):
                continue
            
            code_lines += 1
        
        return code_lines

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of code."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

    def _average_function_length(self, tree: ast.AST) -> float:
        """Calculate average function length in lines."""
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        
        if not functions:
            return 0.0
        
        total_lines = sum(
            (n.end_lineno or 0) - (n.lineno or 0) + 1
            for n in functions
            if hasattr(n, "end_lineno") and hasattr(n, "lineno")
        )
        
        return total_lines / len(functions) if functions else 0.0

    def _max_nesting_depth(self, tree: ast.AST, node: ast.AST = None, depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if node is None:
            node = tree
        
        max_depth = depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.FunctionDef, ast.ClassDef)):
                max_depth = max(max_depth, self._max_nesting_depth(tree, child, depth + 1))
            else:
                max_depth = max(max_depth, self._max_nesting_depth(tree, child, depth))
        
        return max_depth

    def _extract_dependencies(self, tree: ast.AST) -> Set[str]:
        """Extract all import dependencies."""
        dependencies = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module.split(".")[0])
        
        return dependencies

    def build_dependency_graph(self, repo_path: Path, ignore_patterns: List[str] = None) -> Dict[str, Any]:
        """Build dependency graph of the codebase."""
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = []
        
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        graph = defaultdict(set)
        file_modules = {}
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                module_name = self._get_module_name(file_path, repo_path)
                file_modules[str(file_path)] = module_name
                
                # Extract imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dep = alias.name.split(".")[0]
                            graph[module_name].add(dep)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dep = node.module.split(".")[0]
                            graph[module_name].add(dep)
            except Exception:
                continue
        
        return {
            "nodes": list(set(list(graph.keys()) + [dep for deps in graph.values() for dep in deps])),
            "edges": [(src, dst) for src, deps in graph.items() for dst in deps],
            "graph": {k: list(v) for k, v in graph.items()},
        }

    def _get_module_name(self, file_path: Path, repo_path: Path) -> str:
        """Get module name from file path."""
        rel_path = file_path.relative_to(repo_path)
        parts = rel_path.parts[:-1] + (rel_path.stem,)
        return ".".join(parts)

    def find_code_smells(self, file_path: Path) -> List[Dict[str, Any]]:
        """Detect code smells in a file."""
        smells = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                        length = (node.end_lineno or 0) - (node.lineno or 0) + 1
                        if length > 50:
                            smells.append({
                                "type": "long_function",
                                "severity": "medium",
                                "location": f"{file_path}:{node.lineno}",
                                "message": f"Function '{node.name}' is {length} lines long (consider breaking it down)",
                            })
                    
                    # Check complexity
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        smells.append({
                            "type": "high_complexity",
                            "severity": "high",
                            "location": f"{file_path}:{node.lineno}",
                            "message": f"Function '{node.name}' has complexity {complexity} (consider refactoring)",
                        })
            
            # Check for deep nesting
            max_depth = self._max_nesting_depth(tree)
            if max_depth > 4:
                smells.append({
                    "type": "deep_nesting",
                    "severity": "medium",
                    "location": f"{file_path}",
                    "message": f"Maximum nesting depth is {max_depth} (consider refactoring)",
                })
            
        except Exception as e:
            smells.append({
                "type": "parse_error",
                "severity": "high",
                "location": str(file_path),
                "message": f"Could not parse file: {e}",
            })
        
        return smells

