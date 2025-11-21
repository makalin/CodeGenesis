# 🧬 Code Genesis

**Adaptive Synthesis Engine for Context-Aware Code Generation**

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/makalin/CodeGenesis?style=social)](https://github.com/makalin/CodeGenesis/stargazers)
[![Discord](https://img.shields.io/discord/999999999999999999?label=Discord&logo=discord&color=7289DA)](link-to-discord-server)

---

## 💡 What is Code Genesis?

**Code Genesis** is more than a standard code generator; it is an **Adaptive Synthesis Engine** designed to learn the unique structure, style, and architectural patterns of your existing codebase. It ensures every line of code it writes looks exactly as if *you* wrote it, guaranteeing seamless integration and maintainability.

Stop fighting with large language models (LLMs) to conform to your standards. **Code Genesis** makes your codebase its foundation.

## ✨ Key Features

* **Style Fingerprinting:** Analyzes your entire repository to learn your specific formatting, naming conventions, and commenting style. Code output is **guaranteed** to match your established standards.
* **Architectural Mapping:** Builds a deep, semantic "System Map" of your project architecture (models, services, dependencies) using **Vector Databases** and **AST Analysis**.
* **Contextual RAG:** Uses Retrieval-Augmented Generation (RAG) to ensure generated code leverages existing classes, functions, and design patterns, preventing architectural drift.
* **Test-Aware Generation:** Automatically suggests or writes unit tests for the features it implements, using your project's chosen testing framework.
* **Self-Correction Loop:** Integrates linters and compilers to automatically fix style violations and compilation errors *before* presenting the final code.

## ⚙️ How It Works (The 3 Phases)

| Phase | Description | Output |
| :--- | :--- | :--- |
| **1. Assimilation** | Crawls the target repository, builds the Style Fingerprint, and maps the architecture. | The "System Map" (Vector Index) |
| **2. Architectural Planning** | Takes the user request and retrieves relevant architectural context from the System Map. | A detailed **Code Blueprint** (Pseudocode & File Structure Changes) |
| **3. Adaptive Weaving** | Generates the code, passes it through the style formatter, and validates it against tests/compilers for seamless integration. | Ready-to-commit code adhering to project standards. |

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* An API key for the chosen LLM (e.g., Gemini, GPT-4, Claude)
* Access to the repository you wish to analyze.

### Installation

```bash
# Clone the repository
git clone [https://github.com/makalin/CodeGenesis.git](https://github.com/makalin/CodeGenesis.git)
cd CodeGenesis

# Install dependencies
pip install -r requirements.txt
````

### Configuration

1.  Set your API key in your environment variables:
    ```bash
    export GENESIS_LLM_API_KEY='YOUR_API_KEY'
    ```
2.  Configure the target repository in `config.yaml` (default uses the current directory).

### Usage

Run the setup command to assimilate your current project:

```bash
python genesis.py assimilate --repo_path ./
```

Once assimilation is complete, start generating code using a natural language prompt:

```bash
python genesis.py generate "Implement a new secure user login endpoint using OAuth and connect it to the existing UserDatabase model."
```

## 🤝 Contributing

We welcome contributions\! Please check out our [Contributing Guidelines](https://www.google.com/search?q=CONTRIBUTING.md) and feel free to open issues or submit pull requests.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

-----

*Created by Mehmet T. AKALIN* | *[GitHub: @makalin](https://github.com/makalin)*
