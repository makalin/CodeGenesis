"""Vector database integration for architectural mapping."""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from genesis.utils import is_python_file, should_ignore_file, extract_functions_and_classes
from genesis.config import Config


class VectorDatabase:
    """Manages vector database for codebase embeddings."""

    def __init__(self, config: Config):
        """Initialize vector database."""
        self.config = config
        self.persist_dir = Path(config.get("vector_db.persist_directory", "./.genesis_index"))
        self.collection_name = config.get("vector_db.collection_name", "codebase_embeddings")
        self.embedding_model_name = config.get("vector_db.embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Codebase embeddings for Code Genesis"}
            )
            print(f"Created new collection: {self.collection_name}")

    def index_repository(self, repo_path: Path) -> None:
        """Index entire repository in vector database."""
        repo_path = Path(repo_path).resolve()
        ignore_patterns = self.config.get("repository.ignore_patterns", [])
        
        python_files = self._collect_python_files(repo_path, ignore_patterns)
        
        if not python_files:
            print("No Python files found to index.")
            return
        
        print(f"Indexing {len(python_files)} Python files...")
        
        documents = []
        metadatas = []
        ids = []
        
        for file_path in tqdm(python_files, desc="Indexing files"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                # Extract code structure
                structure = extract_functions_and_classes(tree)
                
                # Create document chunks
                chunks = self._create_chunks(file_path, content, structure, repo_path)
                
                for chunk in chunks:
                    documents.append(chunk["text"])
                    metadatas.append(chunk["metadata"])
                    ids.append(chunk["id"])
                
            except Exception as e:
                print(f"Warning: Could not index {file_path}: {e}")
                continue
        
        if documents:
            # Generate embeddings
            print("Generating embeddings...")
            embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
            
            # Add to collection
            print("Adding to vector database...")
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            
            print(f"Successfully indexed {len(documents)} code chunks.")

    def _collect_python_files(self, repo_path: Path, ignore_patterns: List[str]) -> List[Path]:
        """Collect all Python files in repository."""
        python_files = []
        
        for file_path in repo_path.rglob("*.py"):
            if not should_ignore_file(file_path, ignore_patterns):
                python_files.append(file_path)
        
        return python_files

    def _create_chunks(
        self, file_path: Path, content: str, structure: Dict[str, List[Dict[str, Any]]], repo_path: Path
    ) -> List[Dict[str, Any]]:
        """Create document chunks from file."""
        chunks = []
        rel_path = file_path.relative_to(repo_path)
        
        # Full file chunk
        chunks.append({
            "id": f"{rel_path}::full",
            "text": f"File: {rel_path}\n\n{content}",
            "metadata": {
                "file_path": str(rel_path),
                "type": "full_file",
                "functions": len(structure.get("functions", [])),
                "classes": len(structure.get("classes", [])),
            },
        })
        
        # Function chunks
        for func in structure.get("functions", [])[:10]:  # Limit to avoid too many chunks
            func_text = f"Function: {func['name']}\n"
            if func.get("docstring"):
                func_text += f"Docstring: {func['docstring']}\n"
            func_text += f"Arguments: {', '.join(func.get('args', []))}\n"
            
            chunks.append({
                "id": f"{rel_path}::function::{func['name']}",
                "text": f"File: {rel_path}\n{func_text}",
                "metadata": {
                    "file_path": str(rel_path),
                    "type": "function",
                    "name": func["name"],
                },
            })
        
        # Class chunks
        for cls in structure.get("classes", [])[:10]:
            cls_text = f"Class: {cls['name']}\n"
            if cls.get("docstring"):
                cls_text += f"Docstring: {cls['docstring']}\n"
            cls_text += f"Methods: {', '.join(cls.get('methods', []))}\n"
            
            chunks.append({
                "id": f"{rel_path}::class::{cls['name']}",
                "text": f"File: {rel_path}\n{cls_text}",
                "metadata": {
                    "file_path": str(rel_path),
                    "type": "class",
                    "name": cls["name"],
                },
            })
        
        return chunks

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant code in vector database."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
        )
        
        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        
        return formatted_results

    def clear(self) -> None:
        """Clear the vector database."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Codebase embeddings for Code Genesis"}
            )
            print(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            print(f"Error clearing collection: {e}")

