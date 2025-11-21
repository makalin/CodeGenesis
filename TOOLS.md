# Code Genesis Tools & Functions

Code Genesis includes a comprehensive set of tools and functions for code analysis, refactoring, documentation, and more.

## 📊 Code Analysis Tools

### CodeAnalyzer

Analyze code complexity, metrics, and dependencies.

**Features:**
- Lines of code analysis
- Cyclomatic complexity calculation
- Function and class counting
- Dependency extraction
- Code smell detection
- Dependency graph generation

**Example:**
```python
from genesis.analysis import CodeAnalyzer

analyzer = CodeAnalyzer()
results = analyzer.analyze_repository(Path("./"))
print(f"Total LOC: {results['total_lines_of_code']}")
print(f"Average complexity: {results['average_complexity']}")
```

**CLI:**
```bash
python genesis.py analyze --repo-path ./ --output analysis.json
```

## 🔍 Code Search Tools

### CodeSearcher

Advanced code search functionality with multiple search methods.

**Features:**
- Semantic search (vector-based)
- Regex/grep search
- Function/class finding
- Import tracking
- Usage analysis
- Similar code detection

**Example:**
```python
from genesis.search import CodeSearcher
from genesis.vector_db import VectorDatabase
from genesis.config import Config

config = Config()
vector_db = VectorDatabase(config)
searcher = CodeSearcher(vector_db, config)

# Semantic search
results = searcher.semantic_search("user authentication")

# Find function
functions = searcher.find_function("login_user", repo_path)
```

**CLI:**
```bash
# Semantic search
python genesis.py search "user authentication" --type semantic

# Find function
python genesis.py search "login_user" --type function

# Grep search
python genesis.py search "def.*auth" --type grep
```

## 🔧 Refactoring Tools

### RefactoringTool

Suggest and apply code refactorings.

**Features:**
- Automatic refactoring suggestions
- Code refactoring with LLM
- Symbol renaming
- Function extraction
- Pattern migration

**Example:**
```python
from genesis.refactor import RefactoringTool
from genesis.config import Config

config = Config()
tool = RefactoringTool(config)

# Get suggestions
suggestions = tool.suggest_refactorings(Path("file.py"))

# Apply refactoring
refactored = tool.refactor_code(
    Path("file.py"),
    "extract_method",
    "Extract validation logic into separate function"
)
```

**CLI:**
```bash
python genesis.py refactor file.py --output refactored.py
```

## 📚 Documentation Tools

### DocumentationGenerator

Generate comprehensive documentation for your codebase.

**Features:**
- Function/class docstring generation
- Module docstring generation
- README generation
- API documentation (Markdown)
- Style-aware documentation

**Example:**
```python
from genesis.documentation import DocumentationGenerator
from genesis.config import Config

config = Config()
generator = DocumentationGenerator(config)

# Generate API docs
results = generator.generate_api_docs(repo_path, output_dir)

# Generate docstring
docstring = generator.generate_docstring(Path("file.py"), "my_function")
```

**CLI:**
```bash
python genesis.py docs --repo-path ./ --output-dir ./docs
```

## 🔒 Security Tools

### SecurityScanner

Scan codebase for security vulnerabilities.

**Features:**
- SQL injection detection
- Command injection detection
- Path traversal detection
- Hardcoded secrets detection
- Weak cryptography detection
- Code injection detection

**Example:**
```python
from genesis.security import SecurityScanner

scanner = SecurityScanner()
results = scanner.scan_repository(Path("./"))

for vuln in results['vulnerabilities']:
    if vuln['severity'] == 'high':
        print(f"High severity: {vuln['file']}:{vuln['line']}")
```

**CLI:**
```bash
python genesis.py security-scan --repo-path ./ --output scan.json
```

## 📦 Batch Processing

### BatchProcessor

Process multiple generation requests from a file.

**Features:**
- Batch file processing (JSON or text)
- Template processing with variables
- Progress tracking

**Example:**
```python
from genesis.batch import BatchProcessor
from genesis.config import Config

config = Config()
processor = BatchProcessor(config)

# Process batch file
results = processor.process_batch_file(Path("requests.json"))
```

**CLI:**
```bash
python genesis.py batch requests.json --output-dir ./generated
```

### InteractiveMode

Interactive command-line mode for Code Genesis.

**Features:**
- Interactive prompts
- Command history
- Real-time code generation
- Status checking

**CLI:**
```bash
python genesis.py interactive
```

## 🔄 Git Integration

### GitIntegration

Integrate with Git for version control.

**Features:**
- Feature branch creation
- Automatic commits
- Pull request info generation
- Diff viewing
- File history
- Stash management

**Example:**
```python
from genesis.git_tools import GitIntegration

git = GitIntegration(Path("./"))

# Create feature branch
git.create_feature_branch("feature/new-endpoint")

# Commit generated code
git.commit_generated_code(
    [Path("generated_code.py")],
    "Add new endpoint"
)
```

### CodeReviewGenerator

Generate code reviews using LLM.

**Features:**
- File-level reviews
- Diff reviews
- Review summaries
- Comprehensive feedback

**Example:**
```python
from genesis.git_tools import CodeReviewGenerator
from genesis.config import Config

config = Config()
reviewer = CodeReviewGenerator(config)

# Review file
review = reviewer.review_file(Path("file.py"))

# Review diff
diff_review = reviewer.review_diff(git_diff_string)
```

## 🎯 Usage Examples

### Complete Workflow

```python
from genesis import (
    CodeGenesisEngine,
    CodeAnalyzer,
    SecurityScanner,
    DocumentationGenerator,
)
from pathlib import Path

# Initialize
engine = CodeGenesisEngine()

# 1. Assimilate
engine.assimilate(Path("./"))

# 2. Generate code
result = engine.generate("Create a REST API endpoint")

# 3. Analyze
analyzer = CodeAnalyzer()
analysis = analyzer.analyze_repository(Path("./"))

# 4. Security scan
scanner = SecurityScanner()
security = scanner.scan_repository(Path("./"))

# 5. Generate docs
docs_gen = DocumentationGenerator(engine.config)
docs = docs_gen.generate_api_docs(Path("./"), Path("./docs"))
```

## 📋 All Available CLI Commands

```bash
# Core commands
python genesis.py assimilate          # Build system map
python genesis.py generate "prompt"   # Generate code
python genesis.py status              # Show status
python genesis.py clear               # Clear index

# Analysis & Search
python genesis.py analyze             # Code analysis
python genesis.py search "query"      # Search codebase
python genesis.py security-scan       # Security scan

# Refactoring & Documentation
python genesis.py refactor file.py   # Refactor code
python genesis.py docs               # Generate docs

# Batch & Interactive
python genesis.py batch file.json    # Batch processing
python genesis.py interactive        # Interactive mode
```

## 🔌 Extending Code Genesis

All tools are designed to be extensible. You can:

1. **Create custom analyzers** by extending `CodeAnalyzer`
2. **Add new search methods** to `CodeSearcher`
3. **Implement custom refactorings** in `RefactoringTool`
4. **Add security patterns** to `SecurityScanner`
5. **Create custom CLI commands** in `genesis/cli.py`

## 📖 API Reference

For detailed API documentation, see the generated API docs:

```bash
python genesis.py docs --output-dir ./docs
```

Then open `./docs/API.md` for complete API reference.

