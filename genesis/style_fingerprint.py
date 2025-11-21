"""Style fingerprinting module for analyzing codebase style."""

import ast
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from tqdm import tqdm

from genesis.utils import (
    is_python_file,
    should_ignore_file,
    extract_imports,
    extract_functions_and_classes,
    analyze_indentation,
    analyze_naming_conventions,
    analyze_comments,
)


class StyleFingerprint:
    """Analyzes and stores codebase style patterns."""

    def __init__(self, config: Any):
        """Initialize style fingerprint analyzer."""
        self.config = config
        self.fingerprint: Dict[str, Any] = {
            "indentation": {},
            "naming": {},
            "comments": {},
            "imports": {},
            "structure": {},
            "files_analyzed": 0,
        }

    def analyze_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze entire repository to build style fingerprint."""
        repo_path = Path(repo_path).resolve()
        ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        python_files = self._collect_python_files(repo_path, ignore_patterns)
        
        if not python_files:
            return self.fingerprint
        
        print(f"Analyzing {len(python_files)} Python files for style patterns...")
        
        indentation_stats = []
        naming_stats = []
        comment_stats = []
        import_stats = defaultdict(list)
        structure_stats = {"functions": [], "classes": []}
        
        for file_path in tqdm(python_files, desc="Analyzing files"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                # Analyze indentation
                indent_info = analyze_indentation(content)
                indentation_stats.append(indent_info)
                
                # Analyze naming
                naming_info = analyze_naming_conventions(tree)
                naming_stats.append(naming_info)
                
                # Analyze comments
                comment_info = analyze_comments(content)
                comment_stats.append(comment_info)
                
                # Analyze imports
                imports = extract_imports(tree)
                for category, items in imports.items():
                    import_stats[category].extend(items)
                
                # Analyze structure
                structure = extract_functions_and_classes(tree)
                structure_stats["functions"].extend(structure["functions"])
                structure_stats["classes"].extend(structure["classes"])
                
                self.fingerprint["files_analyzed"] += 1
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue
        
        # Aggregate statistics
        self._aggregate_indentation(indentation_stats)
        self._aggregate_naming(naming_stats)
        self._aggregate_comments(comment_stats)
        self._aggregate_imports(import_stats)
        self._aggregate_structure(structure_stats)
        
        return self.fingerprint

    def _collect_python_files(self, repo_path: Path, ignore_patterns: List[str]) -> List[Path]:
        """Collect all Python files in repository."""
        python_files = []
        
        for file_path in repo_path.rglob("*.py"):
            if not should_ignore_file(file_path, ignore_patterns):
                python_files.append(file_path)
        
        return python_files

    def _aggregate_indentation(self, stats: List[Dict[str, Any]]) -> None:
        """Aggregate indentation statistics."""
        if not stats:
            return
        
        tabs_count = sum(s.get("tabs_count", 0) for s in stats)
        spaces_count = sum(s.get("spaces_count", 0) for s in stats)
        indent_sizes = [s.get("indent_size", 4) for s in stats]
        
        most_common_indent = max(set(indent_sizes), key=indent_sizes.count) if indent_sizes else 4
        
        self.fingerprint["indentation"] = {
            "uses_tabs": tabs_count > spaces_count,
            "indent_size": most_common_indent,
            "preference": "tabs" if tabs_count > spaces_count else "spaces",
        }

    def _aggregate_naming(self, stats: List[Dict[str, Any]]) -> None:
        """Aggregate naming convention statistics."""
        if not stats:
            return
        
        function_patterns = [s.get("function_naming", "snake_case") for s in stats]
        class_patterns = [s.get("class_naming", "PascalCase") for s in stats]
        
        most_common_function = max(set(function_patterns), key=function_patterns.count) if function_patterns else "snake_case"
        most_common_class = max(set(class_patterns), key=class_patterns.count) if class_patterns else "PascalCase"
        
        self.fingerprint["naming"] = {
            "functions": most_common_function,
            "classes": most_common_class,
            "variables": "snake_case",  # Default for Python
        }

    def _aggregate_comments(self, stats: List[Dict[str, Any]]) -> None:
        """Aggregate comment statistics."""
        if not stats:
            return
        
        docstring_styles = [s.get("docstring_style") for s in stats if s.get("docstring_style")]
        avg_comment_freq = sum(s.get("comment_frequency", 0) for s in stats) / len(stats) if stats else 0
        
        most_common_docstring = max(set(docstring_styles), key=docstring_styles.count) if docstring_styles else "triple_double"
        
        self.fingerprint["comments"] = {
            "docstring_style": most_common_docstring,
            "comment_frequency": avg_comment_freq,
            "prefers_inline": avg_comment_freq > 0.1,
        }

    def _aggregate_imports(self, import_stats: Dict[str, List[str]]) -> None:
        """Aggregate import statistics."""
        self.fingerprint["imports"] = {
            "standard_libs": list(set(import_stats.get("standard", []))),
            "third_party": list(set(import_stats.get("third_party", []))),
            "local": list(set(import_stats.get("local", []))),
            "common_third_party": self._get_common_imports(import_stats.get("third_party", [])),
        }

    def _get_common_imports(self, imports: List[str]) -> List[str]:
        """Get most common third-party imports."""
        from collections import Counter
        base_modules = [imp.split(".")[0] for imp in imports]
        counter = Counter(base_modules)
        return [module for module, _ in counter.most_common(10)]

    def _aggregate_structure(self, structure_stats: Dict[str, List[Dict[str, Any]]]) -> None:
        """Aggregate code structure statistics."""
        self.fingerprint["structure"] = {
            "total_functions": len(structure_stats["functions"]),
            "total_classes": len(structure_stats["classes"]),
            "sample_functions": structure_stats["functions"][:20],
            "sample_classes": structure_stats["classes"][:20],
        }

    def get_style_guide(self) -> str:
        """Generate a style guide string from fingerprint."""
        fp = self.fingerprint
        guide = []
        
        guide.append("Code Style Guide (Generated from Codebase Analysis):")
        guide.append("=" * 60)
        
        # Indentation
        indent = fp.get("indentation", {})
        guide.append(f"\nIndentation:")
        guide.append(f"  - Use: {indent.get('preference', 'spaces')}")
        guide.append(f"  - Size: {indent.get('indent_size', 4)}")
        
        # Naming
        naming = fp.get("naming", {})
        guide.append(f"\nNaming Conventions:")
        guide.append(f"  - Functions: {naming.get('functions', 'snake_case')}")
        guide.append(f"  - Classes: {naming.get('classes', 'PascalCase')}")
        guide.append(f"  - Variables: {naming.get('variables', 'snake_case')}")
        
        # Comments
        comments = fp.get("comments", {})
        guide.append(f"\nComments:")
        guide.append(f"  - Docstring style: {comments.get('docstring_style', 'triple_double')}")
        
        # Imports
        imports = fp.get("imports", {})
        guide.append(f"\nCommon Imports:")
        for imp in imports.get("common_third_party", [])[:5]:
            guide.append(f"  - {imp}")
        
        return "\n".join(guide)

