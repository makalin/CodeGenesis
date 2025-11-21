"""Code formatting and validation module."""

import ast
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import sys

try:
    import black
except ImportError:
    black = None

# Ruff is a command-line tool, not a Python module
# We'll use subprocess to call it


class CodeFormatter:
    """Handles code formatting and validation."""

    def __init__(self, style_fingerprint: Dict[str, Any]):
        """Initialize code formatter with style fingerprint."""
        self.style_fingerprint = style_fingerprint

    def format_code(self, code: str, file_path: Optional[Path] = None) -> str:
        """Format code according to style fingerprint."""
        formatted = code
        
        # Apply indentation
        formatted = self._apply_indentation(formatted)
        
        # Try to use black if available
        if black:
            try:
                indent_info = self.style_fingerprint.get("indentation", {})
                indent_size = indent_info.get("indent_size", 4)
                line_length = 88  # Black default
                
                mode = black.Mode(
                    line_length=line_length,
                    target_versions={black.TargetVersion.PY311},
                )
                
                formatted = black.format_str(formatted, mode=mode)
            except Exception as e:
                print(f"Warning: Black formatting failed: {e}")
        
        return formatted

    def _apply_indentation(self, code: str) -> str:
        """Apply indentation style from fingerprint."""
        indent_info = self.style_fingerprint.get("indentation", {})
        indent_size = indent_info.get("indent_size", 4)
        use_tabs = indent_info.get("uses_tabs", False)
        
        if use_tabs:
            # Convert spaces to tabs (simplified)
            lines = code.split("\n")
            formatted_lines = []
            for line in lines:
                if line.strip():
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces > 0:
                        tab_count = leading_spaces // indent_size
                        formatted_lines.append("\t" * tab_count + line.lstrip())
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            return "\n".join(formatted_lines)
        
        return code

    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def lint_code(self, code: str, file_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
        """Lint code and return errors."""
        errors = []
        
        # Basic syntax check
        is_valid, syntax_error = self.validate_syntax(code)
        if not is_valid:
            errors.append(f"Syntax error: {syntax_error}")
            return False, errors
        
        # Try ruff if available (command-line tool)
        if file_path:
            try:
                # Check if ruff is available
                subprocess.run(["ruff", "--version"], capture_output=True, check=True)
                
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(code)
                    temp_path = Path(f.name)
                
                try:
                    result = subprocess.run(
                        ["ruff", "check", str(temp_path)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    
                    if result.returncode != 0:
                        errors.extend(result.stdout.split("\n"))
                finally:
                    temp_path.unlink()
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Ruff not available, skip
                pass
            except Exception as e:
                print(f"Warning: Ruff linting failed: {e}")
        
        return len(errors) == 0, errors

    def auto_fix(self, code: str, max_iterations: int = 3) -> Tuple[str, bool]:
        """Attempt to auto-fix code issues."""
        current_code = code
        
        for iteration in range(max_iterations):
            is_valid, _ = self.validate_syntax(current_code)
            if is_valid:
                is_lint_ok, lint_errors = self.lint_code(current_code)
                if is_lint_ok:
                    return current_code, True
            
            # Try to fix common issues
            current_code = self._attempt_fix(current_code)
        
        return current_code, False

    def _attempt_fix(self, code: str) -> str:
        """Attempt to fix common code issues."""
        # Basic fixes
        fixed = code
        
        # Remove trailing whitespace
        lines = fixed.split("\n")
        fixed_lines = [line.rstrip() for line in lines]
        fixed = "\n".join(fixed_lines)
        
        # Ensure final newline
        if fixed and not fixed.endswith("\n"):
            fixed += "\n"
        
        return fixed

