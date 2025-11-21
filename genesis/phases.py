"""Implementation of the three phases: Assimilation, Planning, and Weaving."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from genesis.config import Config
from genesis.style_fingerprint import StyleFingerprint
from genesis.vector_db import VectorDatabase
from genesis.llm_client import create_llm_client, LLMClient
from genesis.code_formatter import CodeFormatter


class Phase1Assimilation:
    """Phase 1: Assimilation - Builds the System Map."""

    def __init__(self, config: Config):
        """Initialize assimilation phase."""
        self.config = config
        self.style_fingerprint = StyleFingerprint(config)
        self.vector_db = VectorDatabase(config)

    def run(self, repo_path: Path) -> Dict[str, Any]:
        """Run assimilation phase."""
        print("\n" + "=" * 60)
        print("PHASE 1: ASSIMILATION")
        print("=" * 60)
        
        repo_path = Path(repo_path).resolve()
        
        # Build style fingerprint
        print("\n[1/2] Building style fingerprint...")
        fingerprint = self.style_fingerprint.analyze_repository(repo_path)
        
        # Build vector database index
        print("\n[2/2] Building architectural map (vector index)...")
        self.vector_db.index_repository(repo_path)
        
        # Save system map
        system_map = {
            "fingerprint": fingerprint,
            "repo_path": str(repo_path),
        }
        
        print("\n✓ Assimilation complete!")
        print(f"  - Files analyzed: {fingerprint.get('files_analyzed', 0)}")
        print(f"  - Vector index: {self.vector_db.collection.count()} chunks")
        
        return system_map


class Phase2ArchitecturalPlanning:
    """Phase 2: Architectural Planning - Creates Code Blueprint."""

    def __init__(self, config: Config, vector_db: VectorDatabase, style_fingerprint: Dict[str, Any]):
        """Initialize planning phase."""
        self.config = config
        self.vector_db = vector_db
        self.style_fingerprint = style_fingerprint
        self.llm_client = create_llm_client(config)

    def run(self, user_request: str) -> Dict[str, Any]:
        """Run architectural planning phase."""
        print("\n" + "=" * 60)
        print("PHASE 2: ARCHITECTURAL PLANNING")
        print("=" * 60)
        
        # Retrieve relevant context from vector database
        print("\n[1/3] Retrieving relevant architectural context...")
        relevant_code = self.vector_db.search(user_request, n_results=5)
        
        context_text = self._format_context(relevant_code)
        
        # Generate code blueprint
        print("\n[2/3] Generating code blueprint...")
        blueprint = self._generate_blueprint(user_request, context_text)
        
        # Validate blueprint
        print("\n[3/3] Validating blueprint...")
        validated_blueprint = self._validate_blueprint(blueprint)
        
        print("\n✓ Architectural planning complete!")
        print(f"  - Files to create/modify: {len(validated_blueprint.get('files', []))}")
        
        return validated_blueprint

    def _format_context(self, relevant_code: List[Dict[str, Any]]) -> str:
        """Format relevant code context for LLM."""
        context_parts = []
        
        for item in relevant_code:
            doc = item.get("document", "")
            metadata = item.get("metadata", {})
            file_path = metadata.get("file_path", "unknown")
            
            context_parts.append(f"--- File: {file_path} ---\n{doc}\n")
        
        return "\n".join(context_parts)

    def _generate_blueprint(self, user_request: str, context: str) -> Dict[str, Any]:
        """Generate code blueprint using LLM."""
        style_guide = StyleFingerprint(self.config).get_style_guide()
        
        system_prompt = f"""You are an expert software architect. Your task is to create a detailed code blueprint based on user requirements.

{style_guide}

Analyze the user request and the provided codebase context, then create a blueprint that includes:
1. List of files to create or modify
2. For each file: detailed pseudocode or structure
3. Dependencies and imports needed
4. Integration points with existing code

Return your response as a JSON object with this structure:
{{
    "files": [
        {{
            "path": "relative/path/to/file.py",
            "action": "create" or "modify",
            "description": "What this file does",
            "pseudocode": "Detailed pseudocode or structure",
            "imports": ["list", "of", "imports"],
            "dependencies": ["list", "of", "dependencies"]
        }}
    ],
    "summary": "Brief summary of the implementation"
}}"""

        user_prompt = f"""User Request: {user_request}

Relevant Codebase Context:
{context}

Create a detailed code blueprint following the existing codebase patterns and style."""
        
        response = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            blueprint = json.loads(response)
            return blueprint
        except json.JSONDecodeError:
            # Fallback: create a simple blueprint
            return {
                "files": [{
                    "path": "generated_code.py",
                    "action": "create",
                    "description": "Generated code based on user request",
                    "pseudocode": response,
                    "imports": [],
                    "dependencies": [],
                }],
                "summary": user_request,
            }

    def _validate_blueprint(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance blueprint."""
        if "files" not in blueprint:
            blueprint["files"] = []
        
        for file_info in blueprint["files"]:
            if "path" not in file_info:
                file_info["path"] = "generated_code.py"
            if "action" not in file_info:
                file_info["action"] = "create"
            if "description" not in file_info:
                file_info["description"] = "Generated code"
            if "pseudocode" not in file_info:
                file_info["pseudocode"] = ""
            if "imports" not in file_info:
                file_info["imports"] = []
            if "dependencies" not in file_info:
                file_info["dependencies"] = []
        
        return blueprint


class Phase3AdaptiveWeaving:
    """Phase 3: Adaptive Weaving - Generates and validates code."""

    def __init__(
        self,
        config: Config,
        vector_db: VectorDatabase,
        style_fingerprint: Dict[str, Any],
        blueprint: Dict[str, Any],
    ):
        """Initialize weaving phase."""
        self.config = config
        self.vector_db = vector_db
        self.style_fingerprint = style_fingerprint
        self.blueprint = blueprint
        self.llm_client = create_llm_client(config)
        self.formatter = CodeFormatter(style_fingerprint)

    def run(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Run adaptive weaving phase."""
        print("\n" + "=" * 60)
        print("PHASE 3: ADAPTIVE WEAVING")
        print("=" * 60)
        
        if output_dir is None:
            output_dir = Path.cwd() / "generated_code"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for file_info in self.blueprint.get("files", []):
            print(f"\n[Generating] {file_info.get('path', 'unknown')}...")
            
            # Generate code
            code = self._generate_code(file_info)
            
            # Format code
            if self.config.get("generation.auto_format", True):
                code = self.formatter.format_code(code)
            
            # Validate and fix
            if self.config.get("generation.auto_lint", True):
                code, is_valid = self._validate_and_fix(code, file_info)
                if not is_valid:
                    print(f"  ⚠ Warning: Code may have issues")
            
            # Write file
            file_path = output_dir / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            generated_files.append({
                "path": str(file_path),
                "action": file_info.get("action", "create"),
                "code": code,
            })
            
            print(f"  ✓ Generated: {file_path}")
        
        # Generate tests if enabled
        if self.config.get("generation.auto_test", True):
            print("\n[Generating] Tests...")
            test_files = self._generate_tests(generated_files, output_dir)
            generated_files.extend(test_files)
        
        print("\n✓ Adaptive weaving complete!")
        print(f"  - Files generated: {len(generated_files)}")
        print(f"  - Output directory: {output_dir}")
        
        return {
            "files": generated_files,
            "output_dir": str(output_dir),
        }

    def _generate_code(self, file_info: Dict[str, Any]) -> str:
        """Generate code for a file."""
        style_guide = StyleFingerprint(self.config).get_style_guide()
        
        # Get relevant context
        query = f"{file_info.get('description', '')} {file_info.get('pseudocode', '')}"
        relevant_code = self.vector_db.search(query, n_results=3)
        context = self._format_context(relevant_code)
        
        system_prompt = f"""You are an expert Python developer. Generate production-ready code that perfectly matches the existing codebase style.

{style_guide}

IMPORTANT:
- Follow the exact indentation style (tabs/spaces, size)
- Use the exact naming conventions (snake_case, camelCase, etc.)
- Match the docstring style
- Use the same import organization
- Follow the same code structure patterns
- Ensure the code is complete, functional, and well-documented"""

        user_prompt = f"""Generate Python code for the following file:

File: {file_info.get('path', 'unknown')}
Description: {file_info.get('description', '')}
Pseudocode/Structure:
{file_info.get('pseudocode', '')}

Required Imports: {', '.join(file_info.get('imports', []))}
Dependencies: {', '.join(file_info.get('dependencies', []))}

Relevant Existing Code:
{context}

Generate the complete, production-ready Python code that integrates seamlessly with the existing codebase."""
        
        code = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
        
        # Clean up code (remove markdown code blocks if present)
        if "```python" in code:
            code_start = code.find("```python") + 9
            code_end = code.find("```", code_start)
            code = code[code_start:code_end].strip()
        elif "```" in code:
            code_start = code.find("```") + 3
            code_end = code.find("```", code_start)
            code = code[code_start:code_end].strip()
        
        return code

    def _format_context(self, relevant_code: List[Dict[str, Any]]) -> str:
        """Format relevant code context."""
        context_parts = []
        
        for item in relevant_code:
            doc = item.get("document", "")
            metadata = item.get("metadata", {})
            file_path = metadata.get("file_path", "unknown")
            
            context_parts.append(f"--- File: {file_path} ---\n{doc}\n")
        
        return "\n".join(context_parts)

    def _validate_and_fix(self, code: str, file_info: Dict[str, Any]) -> Tuple[str, bool]:
        """Validate and attempt to fix code."""
        max_iterations = self.config.get("correction.max_iterations", 3)
        code, is_valid = self.formatter.auto_fix(code, max_iterations=max_iterations)
        return code, is_valid

    def _generate_tests(self, generated_files: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
        """Generate test files for generated code."""
        test_framework = self.config.get("generation.test_framework", "pytest")
        test_files = []
        
        for file_info in generated_files:
            if file_info.get("action") == "create":
                # Generate test file
                test_path = f"test_{Path(file_info['path']).name}"
                
                system_prompt = f"""Generate {test_framework} test cases for the provided code. Ensure tests are comprehensive and follow best practices."""
                
                user_prompt = f"""Generate {test_framework} test cases for:

{file_info.get('code', '')}

Create comprehensive test cases covering:
- Happy path scenarios
- Edge cases
- Error handling
- Integration with existing code"""
                
                test_code = self.llm_client.generate(user_prompt, system_prompt=system_prompt)
                
                # Clean up test code
                if "```python" in test_code:
                    test_start = test_code.find("```python") + 9
                    test_end = test_code.find("```", test_start)
                    test_code = test_code[test_start:test_end].strip()
                elif "```" in test_code:
                    test_start = test_code.find("```") + 3
                    test_end = test_code.find("```", test_start)
                    test_code = test_code[test_start:test_end].strip()
                
                test_file_path = output_dir / "tests" / test_path
                test_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(test_code)
                
                test_files.append({
                    "path": str(test_file_path),
                    "action": "create",
                    "code": test_code,
                })
        
        return test_files

