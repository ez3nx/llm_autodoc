"""
LLM AutoDoc - Automatic documentation generation using LLM for code repositories.

This package provides tools for analyzing code repositories and generating
comprehensive documentation using Large Language Models.
"""

from .services.ast_analyzer import AstAnalyzer
from .services.doc_generator import DocGenerator
from .services.github_parser import GitHubParser
from .services.llm_agent import LlmAgent

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "LlmAgent",
    "GitHubParser",
    "DocGenerator",
    "AstAnalyzer",
]
