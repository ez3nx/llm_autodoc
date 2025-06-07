#!/usr/bin/env python3
"""
Command Line Interface for LLM AutoDoc.

This module provides CLI commands for generating documentation
from code repositories using LLM.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .services.ast_analyzer import AstAnalyzer
from .services.doc_generator import DocGenerator
from .services.github_parser import GitHubParser
from .services.llm_agent import LlmAgent


def generate_docs(
    repo_path: str,
    output_file: str = "README.md",
    model: str = "gemini-flash",
    style: str = "summary",
    github_token: Optional[str] = None,
    openrouter_key: Optional[str] = None,
) -> None:
    """
    Generate documentation for a repository.

    Args:
        repo_path: Path to the repository
        output_file: Output file name (default: README.md)
        model: LLM model to use
        style: Documentation style
        github_token: GitHub API token
        openrouter_key: OpenRouter API key
    """
    print(f"🚀 Starting documentation generation for: {repo_path}")

    # Initialize services
    llm_agent = LlmAgent(
        openrouter_api_key=openrouter_key or os.getenv("OPENROUTER_API_KEY"),
        default_model=model,
    )

    github_parser = GitHubParser(github_token=github_token or os.getenv("GITHUB_TOKEN"))

    doc_generator = DocGenerator()
    ast_analyzer = AstAnalyzer()

    try:
        # Analyze repository structure
        print("📊 Analyzing repository structure...")
        ast_data = ast_analyzer.analyze_directory(repo_path)

        # Parse files content
        print("📖 Reading repository files...")
        files_content = github_parser.parse_local_repository(repo_path)

        # Generate documentation
        print(f"🤖 Generating documentation using {model}...")
        readme_content = llm_agent.generate_readme_content(
            ast_data=ast_data, files_content=files_content, style=style, model_key=model
        )

        # Save to file
        if os.path.isabs(output_file):
            output_path = Path(output_file)
        else:
            output_path = Path(repo_path) / output_file

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"✅ Documentation generated successfully: {output_path}")

    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        sys.exit(1)


def update_docs(
    repo_path: str,
    readme_file: str = "README.md",
    model: str = "gemini-flash",
    style: str = "summary",
    github_token: Optional[str] = None,
    openrouter_key: Optional[str] = None,
) -> None:
    """
    Update existing documentation based on recent changes.

    Args:
        repo_path: Path to the repository
        readme_file: README file to update
        model: LLM model to use
        style: Documentation style
        github_token: GitHub API token
        openrouter_key: OpenRouter API key
    """
    print(f"🔄 Updating documentation for: {repo_path}")

    # Initialize services
    llm_agent = LlmAgent(
        openrouter_api_key=openrouter_key or os.getenv("OPENROUTER_API_KEY"),
        default_model=model,
    )

    github_parser = GitHubParser(github_token=github_token or os.getenv("GITHUB_TOKEN"))

    ast_analyzer = AstAnalyzer()

    try:
        # Read existing README
        readme_path = Path(repo_path) / readme_file
        existing_readme = ""
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                existing_readme = f.read()

        # Analyze repository structure
        print("📊 Analyzing repository structure...")
        ast_data = ast_analyzer.analyze_directory(repo_path)

        # Parse files content
        print("📖 Reading repository files...")
        files_content = github_parser.parse_local_repository(repo_path)

        # Get recent PRs (if GitHub repo)
        recent_prs = []
        try:
            if os.path.exists(os.path.join(repo_path, ".git")):
                # Try to get GitHub repo info and recent PRs
                # This is a simplified version - in real implementation
                # you'd parse git remote to get repo info
                pass
        except Exception:
            pass

        # Update documentation
        print(f"🤖 Updating documentation using {model}...")
        updated_readme = llm_agent.update_readme_content(
            existing_readme=existing_readme,
            recent_prs=recent_prs,
            ast_data=ast_data,
            files_content=files_content,
            style=style,
            model_key=model,
        )

        # Save updated file
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_readme)

        print(f"✅ Documentation updated successfully: {readme_path}")

    except Exception as e:
        print(f"❌ Error updating documentation: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM AutoDoc - Automatic documentation generation using LLM"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate new documentation for a repository"
    )
    generate_parser.add_argument("repo_path", help="Path to the repository")
    generate_parser.add_argument(
        "--output",
        "-o",
        default="README.md",
        help="Output file name (default: README.md)",
    )
    generate_parser.add_argument(
        "--model",
        "-m",
        choices=["claude-sonnet", "gemini-flash", "gpt-4o-mini"],
        default="gemini-flash",
        help="LLM model to use (default: gemini-flash)",
    )
    generate_parser.add_argument(
        "--style",
        "-s",
        choices=["summary", "detailed", "technical"],
        default="summary",
        help="Documentation style (default: summary)",
    )
    generate_parser.add_argument(
        "--github-token", help="GitHub API token (or set GITHUB_TOKEN env var)"
    )
    generate_parser.add_argument(
        "--openrouter-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )

    # Update command
    update_parser = subparsers.add_parser(
        "update", help="Update existing documentation"
    )
    update_parser.add_argument("repo_path", help="Path to the repository")
    update_parser.add_argument(
        "--readme",
        "-r",
        default="README.md",
        help="README file to update (default: README.md)",
    )
    update_parser.add_argument(
        "--model",
        "-m",
        choices=["claude-sonnet", "gemini-flash", "gpt-4o-mini"],
        default="gemini-flash",
        help="LLM model to use (default: gemini-flash)",
    )
    update_parser.add_argument(
        "--style",
        "-s",
        choices=["summary", "detailed", "technical"],
        default="summary",
        help="Documentation style (default: summary)",
    )
    update_parser.add_argument(
        "--github-token", help="GitHub API token (or set GITHUB_TOKEN env var)"
    )
    update_parser.add_argument(
        "--openrouter-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        generate_docs(
            repo_path=args.repo_path,
            output_file=args.output,
            model=args.model,
            style=args.style,
            github_token=args.github_token,
            openrouter_key=args.openrouter_key,
        )
    elif args.command == "update":
        update_docs(
            repo_path=args.repo_path,
            readme_file=args.readme,
            model=args.model,
            style=args.style,
            github_token=args.github_token,
            openrouter_key=args.openrouter_key,
        )


if __name__ == "__main__":
    main()
