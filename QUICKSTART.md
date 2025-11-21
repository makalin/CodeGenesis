# Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your LLM API key:**
   ```bash
   export GENESIS_LLM_API_KEY='your-api-key-here'
   ```
   
   Or for specific providers:
   - OpenAI: `export OPENAI_API_KEY='your-key'`
   - Anthropic: `export ANTHROPIC_API_KEY='your-key'`
   - Google: `export GOOGLE_API_KEY='your-key'`

3. **Configure (optional):**
   Edit `config.yaml` to customize settings.

## Usage

### Step 1: Assimilate Your Repository

Analyze your codebase to build the style fingerprint and architectural map:

```bash
python genesis.py assimilate --repo-path ./
```

This will:
- Analyze all Python files in your repository
- Build a style fingerprint (indentation, naming, comments, etc.)
- Create a vector database index of your codebase architecture

### Step 2: Generate Code

Generate code based on natural language prompts:

```bash
python genesis.py generate "Implement a new secure user login endpoint using OAuth"
```

The generated code will:
- Match your codebase style exactly
- Use existing patterns and architecture
- Include proper imports and dependencies
- Be automatically formatted and validated

### Other Commands

**Check status:**
```bash
python genesis.py status
```

**Clear index:**
```bash
python genesis.py clear
```

## Example Workflow

```bash
# 1. Assimilate your project
python genesis.py assimilate

# 2. Generate a new feature
python genesis.py generate "Create a REST API endpoint for user registration with email validation"

# 3. Check what was generated
ls -la generated_code/
```

## Configuration

Edit `config.yaml` to customize:
- LLM provider and model
- Vector database settings
- Code generation options
- Test framework preferences

## Troubleshooting

**Issue: "LLM API key not found"**
- Make sure you've set the `GENESIS_LLM_API_KEY` environment variable
- Or set provider-specific keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)

**Issue: "No Python files found"**
- Check that your repository path is correct
- Verify ignore patterns in `config.yaml` aren't excluding your files

**Issue: "Import errors"**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

