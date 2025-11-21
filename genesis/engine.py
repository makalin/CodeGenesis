"""Main Code Genesis engine that orchestrates all phases."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from genesis.config import Config
from genesis.style_fingerprint import StyleFingerprint
from genesis.vector_db import VectorDatabase
from genesis.phases import Phase1Assimilation, Phase2ArchitecturalPlanning, Phase3AdaptiveWeaving


class CodeGenesisEngine:
    """Main engine for Code Genesis."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Code Genesis engine."""
        self.config = Config(config_path)
        self.vector_db = VectorDatabase(self.config)
        self.style_fingerprint_data: Optional[Dict[str, Any]] = None
        self.system_map_path = Path(self.config.get("vector_db.persist_directory", "./.genesis_index")) / "system_map.json"

    def assimilate(self, repo_path: Optional[Path] = None) -> Dict[str, Any]:
        """Run Phase 1: Assimilation."""
        if repo_path is None:
            repo_path = self.config.get_repo_path()
        
        phase1 = Phase1Assimilation(self.config)
        system_map = phase1.run(repo_path)
        
        # Save system map
        self.style_fingerprint_data = system_map.get("fingerprint", {})
        self._save_system_map(system_map)
        
        return system_map

    def generate(self, user_request: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Generate code based on user request."""
        # Load system map if available
        system_map = self._load_system_map()
        
        if not system_map:
            print("⚠ Warning: System map not found. Running assimilation first...")
            self.assimilate()
            system_map = self._load_system_map()
        
        self.style_fingerprint_data = system_map.get("fingerprint", {})
        
        # Phase 2: Architectural Planning
        phase2 = Phase2ArchitecturalPlanning(
            self.config,
            self.vector_db,
            self.style_fingerprint_data,
        )
        blueprint = phase2.run(user_request)
        
        # Phase 3: Adaptive Weaving
        phase3 = Phase3AdaptiveWeaving(
            self.config,
            self.vector_db,
            self.style_fingerprint_data,
            blueprint,
        )
        result = phase3.run(output_dir)
        
        return {
            "blueprint": blueprint,
            "generated_files": result,
        }

    def _save_system_map(self, system_map: Dict[str, Any]) -> None:
        """Save system map to disk."""
        self.system_map_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.system_map_path, "w", encoding="utf-8") as f:
            json.dump(system_map, f, indent=2)

    def _load_system_map(self) -> Optional[Dict[str, Any]]:
        """Load system map from disk."""
        if self.system_map_path.exists():
            try:
                with open(self.system_map_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load system map: {e}")
        return None

    def clear_index(self) -> None:
        """Clear the vector database index."""
        self.vector_db.clear()
        if self.system_map_path.exists():
            self.system_map_path.unlink()
        print("✓ Index cleared successfully")

