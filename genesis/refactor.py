"""Code refactoring and migration tools."""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from genesis.llm_client import create_llm_client
from genesis.config import Config
from genesis.style_fingerprint import StyleFingerprint


class RefactoringTool:
    """Tools for code refactoring and migration."""

    def __init__(self, config: Config):
        """Initialize refactoring tool."""
        self.config = config
        self.llm_client = create_llm_client(config)

    def suggest_refactorings(self, file_path: Path) -> List[Dict[str, Any]]:
        """Suggest refactoring opportunities for a file."""
        from genesis.analysis import CodeAnalyzer
        
        analyzer = CodeAnalyzer()
        smells = analyzer.find_code_smells(file_path)
        
        suggestions = []
        for smell in smells:
            if smell["type"] == "long_function":
                suggestions.append({
                    "type": "extract_method",
                    "file": str(file_path),
                    "location": smell["location"],
                    "description": "Extract parts of this long function into smaller functions",
                    "priority": "medium",
                })
            elif smell["type"] == "high_complexity":
                suggestions.append({
                    "type": "simplify_conditionals",
                    "file": str(file_path),
                    "location": smell["location"],
                    "description": "Simplify complex conditionals or extract into separate functions",
                    "priority": "high",
                })
            elif smell["type"] == "deep_nesting":
                suggestions.append({
                    "type": "reduce_nesting",
                    "file": str(file_path),
                    "location": smell["location"],
                    "description": "Use early returns or extract methods to reduce nesting",
                    "priority": "medium",
                })
        
        return suggestions

    def refactor_code(self, file_path: Path, refactoring_type: str, description: str) -> str:
        """Refactor code using LLM."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            style_fp = StyleFingerprint(self.config)
            style_guide = style_fp.get_style_guide()
            
            system_prompt = f"""You are an expert code refactoring assistant. Refactor the provided code according to the request while maintaining:
- Exact same functionality
- Code style from the style guide
- All tests should still pass

{style_guide}

Return only the refactored code, no explanations."""
            
            user_prompt = f"""Refactor the following code using {refactoring_type}:

Description: {description}

Code:
{content}

Provide the complete refactored code."""
            
            refactored = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
            
            # Clean up code
            if "```python" in refactored:
                refactored = refactored.split("```python")[1].split("```")[0].strip()
            elif "```" in refactored:
                refactored = refactored.split("```")[1].split("```")[0].strip()
            
            return refactored
        except Exception as e:
            return f"Error refactoring: {e}"

    def rename_symbol(self, file_path: Path, old_name: str, new_name: str) -> str:
        """Rename a symbol throughout a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple find and replace (could be enhanced with AST)
            # Replace whole word matches only
            pattern = r'\b' + re.escape(old_name) + r'\b'
            refactored = re.sub(pattern, new_name, content)
            
            return refactored
        except Exception as e:
            return f"Error renaming: {e}"

    def extract_function(self, file_path: Path, start_line: int, end_line: int, function_name: str) -> Dict[str, Any]:
        """Extract code block into a new function."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Extract the code block
            extracted_code = "".join(lines[start_line - 1:end_line])
            
            # Generate function signature
            system_prompt = """Analyze the code block and create an appropriate function signature with parameters."""
            
            user_prompt = f"""Create a function signature for this code block:

{extracted_code}

Function name: {function_name}
Return the function definition with proper parameters."""
            
            function_def = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
            
            # Replace code block with function call
            function_call = f"{function_name}()"
            new_lines = lines[:start_line - 1] + [function_call + "\n"] + lines[end_line:]
            
            return {
                "original_file": "".join(lines),
                "refactored_file": "".join(new_lines),
                "extracted_function": function_def,
            }
        except Exception as e:
            return {"error": str(e)}

    def migrate_pattern(self, file_path: Path, old_pattern: str, new_pattern: str) -> str:
        """Migrate code from one pattern to another."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            system_prompt = f"""Migrate code from the old pattern to the new pattern while maintaining functionality.

Old pattern: {old_pattern}
New pattern: {new_pattern}"""
            
            user_prompt = f"""Migrate this code:

{content}

Apply the migration pattern transformation."""
            
            migrated = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
            
            if "```python" in migrated:
                migrated = migrated.split("```python")[1].split("```")[0].strip()
            elif "```" in migrated:
                migrated = migrated.split("```")[1].split("```")[0].strip()
            
            return migrated
        except Exception as e:
            return f"Error migrating: {e}"

