"""Security scanning and vulnerability detection tools."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict


class SecurityScanner:
    """Scan code for security vulnerabilities."""

    def __init__(self):
        """Initialize security scanner."""
        self.vulnerability_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*['\"].*%",
                r"execute\s*\(\s*f['\"]",
                r"query\s*\(\s*['\"].*\+",
            ],
            "command_injection": [
                r"os\.system\s*\(",
                r"subprocess\.call\s*\(",
                r"subprocess\.Popen\s*\(",
                r"eval\s*\(",
                r"exec\s*\(",
            ],
            "path_traversal": [
                r"open\s*\(\s*['\"].*\.\./",
                r"open\s*\(\s*['\"].*\.\.\\\\",
            ],
            "hardcoded_secrets": [
                r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
                r"(password|api_key|secret|token)\s*:\s*['\"][^'\"]+['\"]",
            ],
            "insecure_random": [
                r"random\.random\s*\(",
                r"random\.randint\s*\(",
            ],
            "weak_crypto": [
                r"hashlib\.md5\s*\(",
                r"hashlib\.sha1\s*\(",
            ],
        }

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a file for security vulnerabilities."""
        vulnerabilities = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Pattern-based scanning
            for vuln_type, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count("\n") + 1
                        vulnerabilities.append({
                            "type": vuln_type,
                            "severity": self._get_severity(vuln_type),
                            "file": str(file_path),
                            "line": line_num,
                            "code": self._get_line(content, line_num),
                            "description": self._get_description(vuln_type),
                        })
            
            # AST-based scanning
            try:
                tree = ast.parse(content)
                ast_vulns = self._scan_ast(tree, file_path, content)
                vulnerabilities.extend(ast_vulns)
            except SyntaxError:
                pass
        
        except Exception as e:
            vulnerabilities.append({
                "type": "scan_error",
                "severity": "low",
                "file": str(file_path),
                "description": f"Could not scan file: {e}",
            })
        
        return vulnerabilities

    def _scan_ast(self, tree: ast.AST, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Scan AST for security issues."""
        vulnerabilities = []
        
        for node in ast.walk(tree):
            # Check for eval/exec usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "compile"]:
                        line_num = node.lineno if hasattr(node, "lineno") else 0
                        vulnerabilities.append({
                            "type": "code_injection",
                            "severity": "high",
                            "file": str(file_path),
                            "line": line_num,
                            "code": self._get_line(content, line_num),
                            "description": f"Use of {node.func.id}() can lead to code injection vulnerabilities",
                        })
            
            # Check for hardcoded credentials
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if any(keyword in target.id.lower() for keyword in ["password", "secret", "api_key", "token"]):
                            if isinstance(node.value, (ast.Str, ast.Constant)):
                                line_num = node.lineno if hasattr(node, "lineno") else 0
                                vulnerabilities.append({
                                    "type": "hardcoded_secret",
                                    "severity": "high",
                                    "file": str(file_path),
                                    "line": line_num,
                                    "code": self._get_line(content, line_num),
                                    "description": "Hardcoded credentials detected - use environment variables or secure storage",
                                })
        
        return vulnerabilities

    def scan_repository(self, repo_path: Path, ignore_patterns: List[str] = None) -> Dict[str, Any]:
        """Scan entire repository for security vulnerabilities."""
        from genesis.utils import is_python_file, should_ignore_file
        
        if ignore_patterns is None:
            ignore_patterns = []
        
        python_files = [f for f in repo_path.rglob("*.py") 
                       if is_python_file(f) and not should_ignore_file(f, ignore_patterns)]
        
        all_vulnerabilities = []
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        
        for file_path in python_files:
            vulns = self.scan_file(file_path)
            all_vulnerabilities.extend(vulns)
            
            for vuln in vulns:
                by_type[vuln["type"]].append(vuln)
                by_severity[vuln["severity"]].append(vuln)
        
        return {
            "total_vulnerabilities": len(all_vulnerabilities),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "vulnerabilities": all_vulnerabilities,
            "files_scanned": len(python_files),
        }

    def _get_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type."""
        high_severity = ["sql_injection", "command_injection", "code_injection", "hardcoded_secret"]
        medium_severity = ["path_traversal", "weak_crypto"]
        
        if vuln_type in high_severity:
            return "high"
        elif vuln_type in medium_severity:
            return "medium"
        else:
            return "low"

    def _get_description(self, vuln_type: str) -> str:
        """Get description for vulnerability type."""
        descriptions = {
            "sql_injection": "Potential SQL injection vulnerability - use parameterized queries",
            "command_injection": "Potential command injection vulnerability - validate and sanitize input",
            "path_traversal": "Potential path traversal vulnerability - validate file paths",
            "hardcoded_secrets": "Hardcoded secrets detected - use environment variables",
            "insecure_random": "Insecure random number generation - use secrets module",
            "weak_crypto": "Weak cryptographic hash - use stronger algorithms (SHA-256+)",
            "code_injection": "Code injection risk - avoid eval/exec with user input",
        }
        return descriptions.get(vuln_type, "Security issue detected")

    def _get_line(self, content: str, line_num: int) -> str:
        """Get line content by line number."""
        lines = content.split("\n")
        if 0 < line_num <= len(lines):
            return lines[line_num - 1].strip()
        return ""

