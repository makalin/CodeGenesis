"""
Code Genesis - Adaptive Synthesis Engine for Context-Aware Code Generation
"""

__version__ = "1.0.0"
__author__ = "Mehmet T. AKALIN"

from genesis.engine import CodeGenesisEngine
from genesis.cli import main
from genesis.analysis import CodeAnalyzer
from genesis.search import CodeSearcher
from genesis.refactor import RefactoringTool
from genesis.documentation import DocumentationGenerator
from genesis.security import SecurityScanner
from genesis.batch import BatchProcessor, InteractiveMode
from genesis.git_tools import GitIntegration, CodeReviewGenerator

__all__ = [
    "CodeGenesisEngine",
    "main",
    "CodeAnalyzer",
    "CodeSearcher",
    "RefactoringTool",
    "DocumentationGenerator",
    "SecurityScanner",
    "BatchProcessor",
    "InteractiveMode",
    "GitIntegration",
    "CodeReviewGenerator",
]

