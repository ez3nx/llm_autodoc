# llm_autodoc/services/ast_analyzer.py
from typing import Any, Dict


class AstAnalyzer:
    def __init__(self):
        print("AstAnalyzer инициализирован")

    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Analyze directory structure and return AST data.
        This is a wrapper around analyze_repository for directory-based analysis.
        """
        print(f"[AstAnalyzer] Analyzing directory: {directory_path}")
        # For now, return a simple structure
        # In real implementation, this would scan the directory and analyze files
        return {
            "repository_overview": f"Analyzed directory: {directory_path}",
            "file_details": {
                "example.py": {
                    "type": "python_module",
                    "functions": [
                        {
                            "name": "main",
                            "params": [],
                            "docstring": "Main function.",
                        }
                    ],
                    "classes": [],
                    "imports": ["os", "sys"],
                }
            },
        }

    def analyze_repository(self, files_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Заглушка: Анализирует структуру кода из словаря файлов.
        В реальной реализации будет использовать ast для Python, и другие инструменты для Go/TS.
        """
        print(f"[AstAnalyzer ЗАГЛУШКА] Анализ {len(files_content)} файлов.")
        analysis_results = {}
        for filepath, content in files_content.items():
            if filepath.endswith(".py"):
                analysis_results[filepath] = {
                    "type": "python_module",
                    "functions": [
                        {
                            "name": "greet",
                            "params": ["name"],
                            "docstring": "Greets a person.",
                        }
                    ],
                    "classes": [],
                    "imports": ["os", "sys"],
                }
            elif filepath.endswith(".go"):
                analysis_results[filepath] = {
                    "type": "go_module",
                    "functions": [
                        {
                            "name": "Add",
                            "params": ["a", "b"],
                            "returns": ["int"],
                            "docstring": "Adds two integers.",
                        }
                    ],
                    "structs": [],
                    "imports": ["fmt"],
                }
            else:
                analysis_results[filepath] = {
                    "type": "unknown",
                    "error": "Language not supported by stub",
                }

        print(f"[AstAnalyzer ЗАГЛУШКА] Результат анализа: {analysis_results}")
        return {
            "repository_overview": f"Проанализировано {len(files_content)} файлов.",
            "file_details": analysis_results,
        }
