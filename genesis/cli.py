"""Command-line interface for Code Genesis."""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from genesis.engine import CodeGenesisEngine

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Code Genesis - Adaptive Synthesis Engine for Context-Aware Code Generation."""
    pass


@cli.command()
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to repository to analyze (default: current directory)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def assimilate(repo_path: Path, config: Path):
    """Phase 1: Assimilate repository - Build style fingerprint and architectural map."""
    try:
        config_path = str(config) if config else None
        engine = CodeGenesisEngine(config_path)
        
        if repo_path is None:
            repo_path = engine.config.get_repo_path()
        
        console.print(Panel.fit(
            "[bold cyan]Code Genesis - Assimilation Phase[/bold cyan]",
            border_style="cyan"
        ))
        
        system_map = engine.assimilate(repo_path)
        
        console.print("\n[bold green]✓ Assimilation completed successfully![/bold green]")
        console.print(f"[dim]System map saved to: {engine.system_map_path}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("prompt", required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Output directory for generated code (default: ./generated_code)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def generate(prompt: str, output_dir: Path, config: Path):
    """Phase 2 & 3: Generate code based on natural language prompt."""
    try:
        config_path = str(config) if config else None
        engine = CodeGenesisEngine(config_path)
        
        console.print(Panel.fit(
            "[bold cyan]Code Genesis - Code Generation[/bold cyan]",
            border_style="cyan"
        ))
        console.print(f"[dim]Request: {prompt}[/dim]\n")
        
        result = engine.generate(prompt, output_dir)
        
        console.print("\n[bold green]✓ Code generation completed successfully![/bold green]")
        console.print(f"[dim]Output directory: {result['generated_files'].get('output_dir', 'N/A')}[/dim]")
        
        # Show generated files
        files = result['generated_files'].get('files', [])
        if files:
            console.print("\n[bold]Generated files:[/bold]")
            for file_info in files:
                console.print(f"  • {file_info.get('path', 'unknown')}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def clear(config: Path):
    """Clear the vector database index and system map."""
    try:
        config_path = str(config) if config else None
        engine = CodeGenesisEngine(config_path)
        
        console.print("[yellow]Clearing index...[/yellow]")
        engine.clear_index()
        console.print("[bold green]✓ Index cleared successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def status(config: Path):
    """Show current status of Code Genesis."""
    try:
        config_path = str(config) if config else None
        engine = CodeGenesisEngine(config_path)
        
        system_map = engine._load_system_map()
        
        console.print(Panel.fit(
            "[bold cyan]Code Genesis Status[/bold cyan]",
            border_style="cyan"
        ))
        
        if system_map:
            fingerprint = system_map.get("fingerprint", {})
            files_analyzed = fingerprint.get("files_analyzed", 0)
            vector_count = engine.vector_db.collection.count()
            
            console.print(f"[green]✓ System map loaded[/green]")
            console.print(f"  • Files analyzed: {files_analyzed}")
            console.print(f"  • Vector chunks: {vector_count}")
            console.print(f"  • Repository: {system_map.get('repo_path', 'N/A')}")
        else:
            console.print("[yellow]⚠ System map not found[/yellow]")
            console.print("  Run 'genesis assimilate' to build the system map")
        
        # Check API key
        api_key = engine.config.get_llm_api_key()
        if api_key:
            console.print(f"\n[green]✓ LLM API key configured[/green]")
        else:
            console.print(f"\n[yellow]⚠ LLM API key not found[/yellow]")
            console.print("  Set GENESIS_LLM_API_KEY environment variable")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to repository to analyze",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Output file for analysis results (JSON)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def analyze(repo_path: Path, output: Path, config: Path):
    """Analyze codebase complexity, metrics, and dependencies."""
    try:
        from genesis.analysis import CodeAnalyzer
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        if repo_path is None:
            repo_path = cfg.get_repo_path()
        
        console.print(Panel.fit(
            "[bold cyan]Code Analysis[/bold cyan]",
            border_style="cyan"
        ))
        
        analyzer = CodeAnalyzer()
        ignore_patterns = cfg.get("repository.ignore_patterns", [])
        
        console.print(f"[dim]Analyzing {repo_path}...[/dim]\n")
        results = analyzer.analyze_repository(repo_path, ignore_patterns)
        
        console.print(f"[green]✓ Analysis complete[/green]")
        console.print(f"  • Total files: {results.get('total_files', 0)}")
        console.print(f"  • Lines of code: {results.get('total_lines_of_code', 0):,}")
        console.print(f"  • Average complexity: {results.get('average_complexity', 0):.2f}")
        console.print(f"  • Dependencies: {len(results.get('dependencies', []))}")
        
        if output:
            import json
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"\n[dim]Results saved to: {output}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to repository",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["semantic", "grep", "function", "class", "import"]),
    default="semantic",
    help="Search type",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def search(query: str, repo_path: Path, type: str, config: Path):
    """Search codebase using various methods."""
    try:
        from genesis.search import CodeSearcher
        from genesis.config import Config
        from genesis.vector_db import VectorDatabase
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        if repo_path is None:
            repo_path = cfg.get_repo_path()
        
        vector_db = VectorDatabase(cfg)
        searcher = CodeSearcher(vector_db, cfg)
        
        console.print(f"[dim]Searching for: {query}[/dim]\n")
        
        if type == "semantic":
            results = searcher.semantic_search(query)
        elif type == "grep":
            results = searcher.grep_search(query, repo_path)
        elif type == "function":
            results = searcher.find_function(query, repo_path)
        elif type == "class":
            results = searcher.find_class(query, repo_path)
        elif type == "import":
            results = searcher.find_imports(query, repo_path)
        else:
            results = []
        
        console.print(f"[green]✓ Found {len(results)} results[/green]\n")
        
        for i, result in enumerate(results[:10], 1):  # Show first 10
            if "file" in result:
                console.print(f"{i}. {result.get('file', 'unknown')}:{result.get('line', '?')}")
                if "content" in result:
                    console.print(f"   {result['content'][:80]}...")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def interactive(config: Path):
    """Start interactive mode."""
    try:
        from genesis.batch import InteractiveMode
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        interactive_mode = InteractiveMode(cfg)
        interactive_mode.start()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Output file for refactored code",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def refactor(file_path: Path, output: Path, config: Path):
    """Suggest and apply refactorings to a file."""
    try:
        from genesis.refactor import RefactoringTool
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        tool = RefactoringTool(cfg)
        suggestions = tool.suggest_refactorings(file_path)
        
        console.print(f"[bold]Refactoring suggestions for {file_path}:[/bold]\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"{i}. [{suggestion['priority']}] {suggestion['type']}")
            console.print(f"   {suggestion['description']}")
            console.print(f"   Location: {suggestion['location']}\n")
        
        if output and suggestions:
            # Apply first suggestion as example
            first = suggestions[0]
            refactored = tool.refactor_code(file_path, first["type"], first["description"])
            with open(output, "w") as f:
                f.write(refactored)
            console.print(f"[green]✓ Refactored code saved to: {output}[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to repository",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Output directory for documentation",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def docs(repo_path: Path, output_dir: Path, config: Path):
    """Generate documentation for the codebase."""
    try:
        from genesis.documentation import DocumentationGenerator
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        if repo_path is None:
            repo_path = cfg.get_repo_path()
        
        if output_dir is None:
            output_dir = Path.cwd() / "docs"
        
        generator = DocumentationGenerator(cfg)
        
        console.print(f"[dim]Generating API documentation...[/dim]\n")
        results = generator.generate_api_docs(repo_path, output_dir)
        
        console.print(f"[green]✓ Documentation generated[/green]")
        console.print(f"  • Files documented: {results.get('files_documented', 0)}")
        console.print(f"  • Output: {results.get('output_file', 'N/A')}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to repository to scan",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Output file for scan results (JSON)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def security_scan(repo_path: Path, output: Path, config: Path):
    """Scan codebase for security vulnerabilities."""
    try:
        from genesis.security import SecurityScanner
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        if repo_path is None:
            repo_path = cfg.get_repo_path()
        
        console.print(Panel.fit(
            "[bold cyan]Security Scan[/bold cyan]",
            border_style="cyan"
        ))
        
        scanner = SecurityScanner()
        ignore_patterns = cfg.get("repository.ignore_patterns", [])
        
        console.print(f"[dim]Scanning {repo_path}...[/dim]\n")
        results = scanner.scan_repository(repo_path, ignore_patterns)
        
        console.print(f"[green]✓ Scan complete[/green]")
        console.print(f"  • Files scanned: {results.get('files_scanned', 0)}")
        console.print(f"  • Total vulnerabilities: {results.get('total_vulnerabilities', 0)}")
        
        by_severity = results.get('by_severity', {})
        if by_severity:
            console.print(f"\n[bold]By Severity:[/bold]")
            for severity, count in by_severity.items():
                color = "red" if severity == "high" else "yellow" if severity == "medium" else "dim"
                console.print(f"  • [{color}]{severity}: {count}[/{color}]")
        
        by_type = results.get('by_type', {})
        if by_type:
            console.print(f"\n[bold]By Type:[/bold]")
            for vuln_type, count in by_type.items():
                console.print(f"  • {vuln_type}: {count}")
        
        if output:
            import json
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"\n[dim]Results saved to: {output}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument("batch_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Output directory for generated code",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def batch(batch_file: Path, output_dir: Path, config: Path):
    """Process batch file with multiple generation requests."""
    try:
        from genesis.batch import BatchProcessor
        from genesis.config import Config
        
        config_path = str(config) if config else None
        cfg = Config(config_path)
        
        processor = BatchProcessor(cfg)
        
        console.print(f"[dim]Processing batch file: {batch_file}[/dim]\n")
        results = processor.process_batch_file(batch_file, output_dir)
        
        console.print(f"[green]✓ Batch processing complete[/green]")
        console.print(f"  • Total: {results.get('total', 0)}")
        console.print(f"  • Successful: {results.get('successful', 0)}")
        console.print(f"  • Failed: {results.get('failed', 0)}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()

