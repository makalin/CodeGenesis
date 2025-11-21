"""Utility functions for Code Genesis."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def is_python_file(file_path: Path) -> bool:
    """Check if file is a Python file."""
    return file_path.suffix == ".py"


def should_ignore_file(file_path: Path, ignore_patterns: List[str]) -> bool:
    """Check if file should be ignored based on patterns."""
    from pathspec import PathSpec
    
    spec = PathSpec.from_lines("gitwildmatch", ignore_patterns)
    return spec.match_file(str(file_path))


def extract_imports(ast_tree: ast.AST) -> Dict[str, List[str]]:
    """Extract import statements from AST."""
    imports = {"standard": [], "third_party": [], "local": []}
    
    standard_libs = {
        "os", "sys", "json", "yaml", "pathlib", "typing", "collections",
        "itertools", "functools", "datetime", "time", "re", "math", "random",
        "string", "io", "csv", "xml", "html", "urllib", "http", "socket",
        "threading", "multiprocessing", "asyncio", "logging", "unittest",
        "doctest", "pdb", "pickle", "sqlite3", "hashlib", "base64", "uuid",
        "ast", "subprocess", "tempfile", "hashlib", "pathlib",
    }
    
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in standard_libs:
                    imports["standard"].append(alias.name)
                else:
                    imports["third_party"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if module in standard_libs:
                    imports["standard"].append(node.module)
                elif not node.module.startswith("."):
                    imports["third_party"].append(node.module)
                else:
                    imports["local"].append(node.module)
    
    return imports


def extract_functions_and_classes(ast_tree: ast.AST) -> Dict[str, List[Dict[str, Any]]]:
    """Extract functions and classes from AST."""
    result = {"functions": [], "classes": []}
    
    # Helper to unparse AST nodes
    def unparse_node(node):
        """Unparse AST node, with fallback for older Python versions."""
        if hasattr(ast, "unparse"):
            return ast.unparse(node)
        try:
            import astunparse
            return astunparse.unparse(node)
        except ImportError:
            return str(node)
    
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            result["functions"].append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "decorators": [unparse_node(d) for d in node.decorator_list],
                "docstring": ast.get_docstring(node),
            })
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            result["classes"].append({
                "name": node.name,
                "bases": [unparse_node(b) for b in node.bases],
                "methods": methods,
                "docstring": ast.get_docstring(node),
            })
    
    return result


def analyze_indentation(content: str) -> Dict[str, Any]:
    """Analyze indentation style."""
    lines = content.split("\n")
    spaces = 0
    tabs = 0
    indent_sizes = []
    
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                if line[0] == "\t":
                    tabs += 1
                else:
                    spaces += 1
                    indent_sizes.append(indent)
    
    if indent_sizes:
        most_common = max(set(indent_sizes), key=indent_sizes.count)
    else:
        most_common = 4
    
    return {
        "uses_tabs": tabs > spaces,
        "indent_size": most_common,
        "spaces_count": spaces,
        "tabs_count": tabs,
    }


def analyze_naming_conventions(ast_tree: ast.AST) -> Dict[str, Any]:
    """Analyze naming conventions."""
    conventions = {
        "functions": [],
        "classes": [],
        "variables": [],
        "constants": [],
    }
    
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            conventions["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            conventions["classes"].append(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            # Check if it's a constant (uppercase name)
            if node.id.isupper():
                conventions["constants"].append(node.id)
            else:
                conventions["variables"].append(node.id)
    
    # Analyze patterns
    function_pattern = _detect_pattern(conventions["functions"])
    class_pattern = _detect_pattern(conventions["classes"])
    
    return {
        "function_naming": function_pattern,
        "class_naming": class_pattern,
        "sample_functions": conventions["functions"][:10],
        "sample_classes": conventions["classes"][:10],
    }


def _detect_pattern(names: List[str]) -> str:
    """Detect naming pattern (snake_case, camelCase, PascalCase)."""
    if not names:
        return "snake_case"
    
    snake_case = sum(1 for n in names if "_" in n and n.islower())
    camel_case = sum(1 for n in names if n[0].islower() and any(c.isupper() for c in n[1:]) and "_" not in n)
    pascal_case = sum(1 for n in names if n[0].isupper() and "_" not in n)
    
    if snake_case >= camel_case and snake_case >= pascal_case:
        return "snake_case"
    elif camel_case >= pascal_case:
        return "camelCase"
    else:
        return "PascalCase"


def analyze_comments(content: str) -> Dict[str, Any]:
    """Analyze comment style."""
    lines = content.split("\n")
    inline_comments = 0
    block_comments = 0
    docstring_style = None
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if "#" in line.split('"')[0] if '"' in line else True:
                inline_comments += 1
        elif '"""' in line or "'''" in line:
            block_comments += 1
    
    # Check for docstring style
    if '"""' in content:
        docstring_style = 'triple_double'
    elif "'''" in content:
        docstring_style = 'triple_single'
    
    return {
        "inline_comments": inline_comments,
        "block_comments": block_comments,
        "docstring_style": docstring_style,
        "comment_frequency": inline_comments / len(lines) if lines else 0,
    }

