"""Batch processing and interactive mode tools."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from genesis.engine import CodeGenesisEngine
from genesis.config import Config


class BatchProcessor:
    """Handle batch code generation from files."""

    def __init__(self, config: Config):
        """Initialize batch processor."""
        self.config = config
        self.engine = CodeGenesisEngine()

    def process_batch_file(self, batch_file: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Process a batch file with multiple generation requests."""
        try:
            with open(batch_file, "r", encoding="utf-8") as f:
                if batch_file.suffix == ".json":
                    batch_data = json.load(f)
                else:
                    # Assume one request per line
                    batch_data = {"requests": [{"prompt": line.strip()} for line in f if line.strip()]}
            
            results = []
            
            for i, request in enumerate(tqdm(batch_data.get("requests", []), desc="Processing batch")):
                prompt = request.get("prompt", "")
                if not prompt:
                    continue
                
                try:
                    result = self.engine.generate(prompt, output_dir)
                    results.append({
                        "request": request,
                        "status": "success",
                        "result": result,
                    })
                except Exception as e:
                    results.append({
                        "request": request,
                        "status": "error",
                        "error": str(e),
                    })
            
            return {
                "total": len(results),
                "successful": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] == "error"),
                "results": results,
            }
        except Exception as e:
            return {"error": str(e)}

    def process_template(self, template_file: Path, variables: Dict[str, Any], output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Process a template file with variable substitution."""
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Simple variable substitution
            for key, value in variables.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            
            # Generate code from template
            result = self.engine.generate(template, output_dir)
            return result
        except Exception as e:
            return {"error": str(e)}


class InteractiveMode:
    """Interactive command mode for Code Genesis."""

    def __init__(self, config: Config):
        """Initialize interactive mode."""
        self.config = config
        self.engine = CodeGenesisEngine()
        self.history: List[Dict[str, Any]] = []

    def start(self):
        """Start interactive mode."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        
        console = Console()
        
        console.print(Panel.fit(
            "[bold cyan]Code Genesis - Interactive Mode[/bold cyan]\n"
            "Type 'help' for commands, 'exit' to quit",
            border_style="cyan"
        ))
        
        while True:
            try:
                command = Prompt.ask("\n[bold]genesis>[/bold]")
                
                if not command.strip():
                    continue
                
                if command.lower() in ["exit", "quit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif command.lower() == "help":
                    self._show_help(console)
                elif command.lower().startswith("generate "):
                    prompt = command[9:].strip()
                    if prompt:
                        self._handle_generate(console, prompt)
                elif command.lower() == "status":
                    self._handle_status(console)
                elif command.lower() == "history":
                    self._handle_history(console)
                elif command.lower().startswith("clear"):
                    self._handle_clear(console)
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except EOFError:
                break

    def _show_help(self, console):
        """Show help message."""
        help_text = """
[bold]Available Commands:[/bold]

  generate <prompt>  - Generate code from natural language prompt
  status            - Show current system status
  history           - Show generation history
  clear             - Clear the vector index
  help              - Show this help message
  exit/quit         - Exit interactive mode
        """
        console.print(help_text)

    def _handle_generate(self, console, prompt: str):
        """Handle generate command."""
        console.print(f"[dim]Generating code for: {prompt}[/dim]\n")
        
        try:
            result = self.engine.generate(prompt)
            self.history.append({"prompt": prompt, "result": result})
            
            console.print("[bold green]✓ Code generated successfully![/bold green]")
            files = result.get("generated_files", {}).get("files", [])
            if files:
                console.print(f"[dim]Generated {len(files)} file(s)[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    def _handle_status(self, console):
        """Handle status command."""
        system_map = self.engine._load_system_map()
        
        if system_map:
            fingerprint = system_map.get("fingerprint", {})
            files_analyzed = fingerprint.get("files_analyzed", 0)
            vector_count = self.engine.vector_db.collection.count()
            
            console.print(f"[green]✓ System map loaded[/green]")
            console.print(f"  • Files analyzed: {files_analyzed}")
            console.print(f"  • Vector chunks: {vector_count}")
        else:
            console.print("[yellow]⚠ System map not found[/yellow]")
            console.print("  Run 'genesis assimilate' first")

    def _handle_history(self, console):
        """Handle history command."""
        if not self.history:
            console.print("[dim]No history[/dim]")
            return
        
        console.print(f"[bold]Generation History ({len(self.history)} items):[/bold]\n")
        for i, item in enumerate(self.history[-10:], 1):  # Show last 10
            console.print(f"{i}. {item['prompt'][:60]}...")

    def _handle_clear(self, console):
        """Handle clear command."""
        self.engine.clear_index()
        console.print("[green]✓ Index cleared[/green]")

