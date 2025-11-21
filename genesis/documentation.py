"""Documentation generation tools."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import ast

from genesis.llm_client import create_llm_client
from genesis.config import Config
from genesis.style_fingerprint import StyleFingerprint


class DocumentationGenerator:
    """Generate documentation for code."""

    def __init__(self, config: Config):
        """Initialize documentation generator."""
        self.config = config
        self.llm_client = create_llm_client(config)

    def generate_docstring(self, file_path: Path, function_name: Optional[str] = None) -> str:
        """Generate docstring for a function or file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            if function_name:
                # Find specific function
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        return self._generate_function_docstring(node, content)
            else:
                # Generate module docstring
                return self._generate_module_docstring(tree, content)
        
        except Exception as e:
            return f"Error generating docstring: {e}"

    def _generate_function_docstring(self, node: ast.FunctionDef, content: str) -> str:
        """Generate docstring for a function."""
        style_fp = StyleFingerprint(self.config)
        fingerprint = style_fp.fingerprint
        docstring_style = fingerprint.get("comments", {}).get("docstring_style", "triple_double")
        
        quote = '"""' if docstring_style == "triple_double" else "'''"
        
        # Extract function signature
        args = [arg.arg for arg in node.args.args]
        returns = "Any"  # Could be enhanced with type hints
        
        system_prompt = f"""Generate a comprehensive docstring in {docstring_style} style following Google/NumPy docstring format."""
        
        user_prompt = f"""Generate a docstring for this function:

Function: {node.name}
Arguments: {', '.join(args)}
Returns: {returns}

Analyze the function body and create a detailed docstring."""
        
        docstring = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        return f"{quote}\n{docstring}\n{quote}"

    def _generate_module_docstring(self, tree: ast.AST, content: str) -> str:
        """Generate module-level docstring."""
        style_fp = StyleFingerprint(self.config)
        fingerprint = style_fp.fingerprint
        docstring_style = fingerprint.get("comments", {}).get("docstring_style", "triple_double")
        
        quote = '"""' if docstring_style == "triple_double" else "'''"
        
        # Analyze module
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        
        system_prompt = "Generate a comprehensive module docstring."
        
        user_prompt = f"""Generate a module docstring for this file:

Functions: {', '.join(functions[:10])}
Classes: {', '.join(classes[:10])}

Create a module-level docstring describing the purpose and main components."""
        
        docstring = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        return f"{quote}\n{docstring}\n{quote}"

    def generate_readme(self, repo_path: Path) -> str:
        """Generate README.md for the repository."""
        from genesis.analysis import CodeAnalyzer
        
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze_repository(repo_path)
        
        system_prompt = """Generate a comprehensive README.md file for a Python project."""
        
        user_prompt = f"""Generate a README.md for this project:

Total files: {analysis.get('total_files', 0)}
Lines of code: {analysis.get('total_lines_of_code', 0)}
Main dependencies: {', '.join(analysis.get('dependencies', [])[:10])}

Create a professional README with:
- Project description
- Installation instructions
- Usage examples
- Features
- Contributing guidelines"""
        
        readme = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        return readme

    def generate_api_docs(self, repo_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Generate API documentation for all modules."""
        from genesis.utils import is_python_file, should_ignore_file
        
        ignore_patterns = self.config.get("repository.ignore_patterns", [])
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        api_docs = {}
        
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                module_doc = {
                    "file": str(file_path),
                    "functions": [],
                    "classes": [],
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        module_doc["functions"].append({
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node),
                            "line": node.lineno,
                        })
                    elif isinstance(node, ast.ClassDef):
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        module_doc["classes"].append({
                            "name": node.name,
                            "methods": methods,
                            "docstring": ast.get_docstring(node),
                            "line": node.lineno,
                        })
                
                api_docs[str(file_path)] = module_doc
            except Exception:
                continue
        
        # Generate markdown documentation
        markdown = self._generate_markdown_docs(api_docs)
        
        output_file = output_dir / "API.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return {
            "files_documented": len(api_docs),
            "output_file": str(output_file),
            "api_docs": api_docs,
        }

    def _generate_markdown_docs(self, api_docs: Dict[str, Any]) -> str:
        """Generate markdown from API docs."""
        lines = ["# API Documentation\n"]
        
        for file_path, doc in api_docs.items():
            lines.append(f"## {file_path}\n")
            
            if doc.get("classes"):
                lines.append("### Classes\n")
                for cls in doc["classes"]:
                    lines.append(f"#### {cls['name']}\n")
                    if cls.get("docstring"):
                        lines.append(f"{cls['docstring']}\n")
                    if cls.get("methods"):
                        lines.append(f"**Methods:** {', '.join(cls['methods'])}\n")
                    lines.append("")
            
            if doc.get("functions"):
                lines.append("### Functions\n")
                for func in doc["functions"]:
                    lines.append(f"#### {func['name']}\n")
                    lines.append(f"**Arguments:** {', '.join(func.get('args', []))}\n")
                    if func.get("docstring"):
                        lines.append(f"{func['docstring']}\n")
                    lines.append("")
        
        return "\n".join(lines)

