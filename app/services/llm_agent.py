# app/services/llm_agent.py
import logging
import os
from typing import Any, Dict, List, Literal, Optional
import requests
from dotenv import load_dotenv
from pathlib import Path

# Configure logging for LLM interactions
logging.basicConfig(level=logging.INFO)
llm_logger = logging.getLogger("llm_agent")


# --- Вспомогательные функции для вызова LLM ---
def _ask_openrouter_llm(
    prompt: str,
    model_name: str,
    api_key: Optional[str],
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    if not api_key:
        print("❌ Ошибка OpenRouter: API ключ не предоставлен.")
        return "⚠️ Ошибка: API ключ для OpenRouter не настроен."
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    url = "https://openrouter.ai/api/v1/chat/completions"

    llm_logger.info(f"🤖 Making LLM request to OpenRouter")
    llm_logger.info(f"📋 Model: {model_name}")
    llm_logger.info(
        f"⚙️ Parameters - Temperature: {temperature}, Max tokens: {max_tokens}"
    )
    llm_logger.info(f"📝 Prompt length: {len(prompt)} characters")
    llm_logger.info(f"🔍 Prompt preview (first 300 chars): {prompt[:300]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        response_json = response.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            content = response_json["choices"][0].get("message", {}).get("content")
            if content:
                llm_logger.info(f"✅ LLM response received successfully")
                llm_logger.info(f"📊 Response length: {len(content)} characters")
                llm_logger.info(
                    f"🔍 Response preview (first 200 chars): {content[:200]}..."
                )
                return content
            else:
                print(
                    f"❌ Ошибка OpenRouter: Неожиданный формат ответа (нет content): {response_json}"
                )
                return "⚠️ Ошибка: Неожиданный формат ответа от OpenRouter."
        else:
            print(
                f"❌ Ошибка OpenRouter: Неожиданный формат ответа (нет choices): {response_json}"
            )
            return "⚠️ Ошибка: Неожиданный формат ответа от OpenRouter."
    except requests.exceptions.HTTPError as e:
        print(f"❌ Ошибка HTTP OpenRouter: {e.response.status_code} {e.response.text}")
        error_message = f"⚠️ Ошибка при обращении к OpenRouter: {e.response.status_code}"
        try:
            error_detail = (
                e.response.json().get("error", {}).get("message", e.response.text)
            )
            error_message += f" - {error_detail}"
        except ValueError:
            pass
        return error_message
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети при запросе к OpenRouter: {e}")
        return f"⚠️ Ошибка сети при обращении к OpenRouter: {e}"
    except Exception as e:
        print(f"❌ Непредвиденная ошибка при запросе к OpenRouter: {e}")
        import traceback

        traceback.print_exc()
        return f"⚠️ Непредвиденная ошибка при обращении к OpenRouter: {e}"


# --- Класс LlmAgent ---
class LlmAgent:
    SUPPORTED_MODELS = Literal["claude-sonnet", "gemini-flash", "gpt-4o-mini"]
    DEFAULT_MODEL_MAPPING = {
        "claude-sonnet": "anthropic/claude-3-sonnet",
        "gemini-flash": "google/gemini-flash-1.5",
        "gpt-4o-mini": "openai/gpt-4o",
    }

    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        default_model: SUPPORTED_MODELS = "gemini-flash",
    ):
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.default_model_key = default_model
        if not self.openrouter_api_key:
            print(
                "ПРЕДУПРЕЖДЕНИЕ: LlmAgent - OpenRouter API ключ не найден! Функционал LLM будет ограничен."
            )
        else:
            print(
                f"LlmAgent инициализирован. OpenRouter API ключ {'есть' if self.openrouter_api_key else 'отсутствует'}."
            )
            print(
                f"Модель по умолчанию: {self.default_model_key} -> {self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)}"
            )

    def _construct_readme_prompt(
        self,
        ast_data: Dict[str, Any],
        files_content: Dict[str, str],
        style: str = "summary",
    ) -> str:
        project_structure_summary = "Основные компоненты проекта:\n"
        if ast_data.get("file_details"):
            for filepath, details in list(ast_data["file_details"].items())[:10]:
                project_structure_summary += (
                    f"- Файл `{filepath}` ({details.get('type', 'unknown')}):\n"
                )
                if "functions" in details and details["functions"]:
                    func_names = [f"`{f['name']}()`" for f in details["functions"][:3]]
                    project_structure_summary += (
                        f"  - Функции: {', '.join(func_names)}\n"
                    )
                if "classes" in details and details["classes"]:
                    class_names = [f"`{c['name']}`" for c in details["classes"][:2]]
                    project_structure_summary += (
                        f"  - Классы: {', '.join(class_names)}\n"
                    )
        else:
            project_structure_summary = (
                "Детальный анализ структуры файлов не представлен."
            )

        # Analyze configuration and setup files for installation/deployment info
        config_files_info = "\n\nИнформация о конфигурации и установке:\n"
        config_found = False

        # Look for dependency management files
        for filepath, content in files_content.items():
            filename = filepath.lower()
            if any(
                config_file in filename
                for config_file in [
                    "requirements.txt",
                    "pyproject.toml",
                    "poetry.lock",
                    "package.json",
                    "go.mod",
                    "cargo.toml",
                    "pom.xml",
                    "build.gradle",
                    "composer.json",
                ]
            ):
                config_files_info += f"- Файл зависимостей: `{filepath}`\n"
                if len(content) < 1000:
                    config_files_info += f"  Содержимое: {content[:500]}...\n"
                config_found = True

        # Look for deployment/docker files
        for filepath, content in files_content.items():
            filename = filepath.lower()
            if any(
                deploy_file in filename
                for deploy_file in [
                    "dockerfile",
                    "docker-compose",
                    "gunicorn.config",
                    ".yml",
                    ".yaml",
                ]
            ) and any(
                keyword in filename
                for keyword in ["docker", "deploy", "config", "ci", "cd"]
            ):
                config_files_info += f"- Файл развертывания: `{filepath}`\n"
                if len(content) < 1000:
                    config_files_info += f"  Содержимое: {content[:500]}...\n"
                config_found = True

        if not config_found:
            config_files_info = ""

        # Analyze project structure
        project_structure_info = "\n\nСтруктура проекта:\n"
        directories = set()
        for filepath in files_content.keys():
            parts = filepath.split("/")
            if len(parts) > 1:
                directories.add(parts[0])

        if directories:
            project_structure_info += "Основные директории:\n"
            for directory in sorted(directories):
                # Count files in each directory
                files_in_dir = [
                    f for f in files_content.keys() if f.startswith(directory + "/")
                ]
                project_structure_info += (
                    f"- `{directory}/` ({len(files_in_dir)} файлов)\n"
                )
        else:
            project_structure_info = ""

        # Include ALL parsed files in the context
        all_files_content = "\n\nВсе файлы проекта:\n"

        # Sort files by importance: main files first, then by extension, then alphabetically
        def file_priority(filepath):
            filename = filepath.lower()
            # Priority 1: Main entry points
            if any(
                main_file in filename
                for main_file in ["main.", "app.", "server.", "index."]
            ):
                return (0, filepath)
            # Priority 2: Configuration files
            elif any(
                config_file in filename
                for config_file in [
                    "requirements.txt",
                    "pyproject.toml",
                    "package.json",
                    "dockerfile",
                    "docker-compose",
                    "gunicorn.config",
                    ".yml",
                    ".yaml",
                ]
            ):
                return (1, filepath)
            # Priority 3: Python files
            elif filename.endswith((".py")):
                return (2, filepath)
            # Priority 4: Other code files
            elif filename.endswith(
                (".go", ".ts", ".js", ".jsx", ".tsx", ".java", ".kt")
            ):
                return (3, filepath)
            # Priority 5: Documentation and config
            elif filename.endswith(
                (".md", ".json", ".toml", ".yml", ".yaml", ".cfg", ".ini")
            ):
                return (4, filepath)
            # Priority 6: Everything else
            else:
                return (5, filepath)

        sorted_files = sorted(files_content.items(), key=lambda x: file_priority(x[0]))

        for filepath, content in sorted_files:
            # Limit content length to avoid token limits
            max_content_length = 2000 if len(files_content) > 10 else 4000
            if len(content) > max_content_length:
                truncated_content = (
                    content[:max_content_length] + "\n... (файл обрезан)"
                )
            else:
                truncated_content = content

            all_files_content += f"\n--- {filepath} ---\n"
            all_files_content += f"Размер: {len(content)} символов\n"
            all_files_content += f"```\n{truncated_content}\n```\n"

        # Keep the old variable name for compatibility
        contextual_code_snippets = all_files_content

        # Log information about files included in prompt
        llm_logger.info(
            f"📄 Including ALL {len(files_content)} files in prompt context"
        )
        total_content_size = sum(len(content) for content in files_content.values())
        llm_logger.info(f"📊 Total content size: {total_content_size} characters")

        # Support for different styles (from colleague's changes)
        if style == "detailed":
            readme_style_instruction = "подробное описание каждого компонента, его назначения, параметров и возвращаемых значений (если применимо)."
            instruction = """Дополнительные инструкции:
        - Включи разделы: Обзор, Возможности, Установка, Использование, Архитектура и Лицензия.
        - Используй четкое форматирование (заголовки, блоки кода, списки).
        - Объясни ключевые компоненты и их взаимодействие.
        """
        else:
            readme_style_instruction = "краткое изложение основных функций и назначения проекта, без излишней детализации."
            instruction = """Дополнительные инструкции:
        - Включи краткое описание проекта, технологический стек и пример использования.
        - Сделай документацию читаемой и дружелюбной для разработчиков.
        """

        prompt = f"""
Ты — опытный технический писатель и разработчик, специализирующийся на создании качественной документации для программных проектов.
Твоя задача — сгенерировать информативный и хорошо структурированный README.md файл для проекта на основе предоставленной информации о его структуре и содержимом некоторых файлов.

**Информация о проекте:**
{ast_data.get("repository_overview", "Обзор проекта не предоставлен.")}

**Анализ структуры кода (из AST):**
{project_structure_summary}

{config_files_info}

{project_structure_info}

{contextual_code_snippets}

**Требования к README.md:**
1.  **Формат:** Строго Markdown.
2.  **Язык:** Русский.
3.  **Стиль документации:** {readme_style_instruction}
4.  **Обязательные разделы (если информация доступна):**
    *   **Название проекта** (придумай подходящее, если не очевидно из данных).
    *   **Описание проекта:** Краткое описание (1-3 предложения) того, что делает проект.
    *   **Основные возможности / Ключевые компоненты:** Опиши основные части проекта, их назначение. Используй данные из анализа структуры кода.
    *   **Основные модули:** Перечисли и опиши назначение основных модулей/пакетов проекта на основе структуры директорий и файлов.
    *   **Технологический стек:** Попробуй определить или предположить основные технологии/языки, используемые в проекте, на основе расширений файлов и импортов.
    *   **Структура проекта:** Опиши организацию директорий и основных файлов проекта. Используй информацию о структуре проекта.
    *   **Установка:** Детальные шаги установки на основе найденных файлов зависимостей (requirements.txt, pyproject.toml, package.json и т.д.). Включи команды клонирования, установки зависимостей, настройки окружения.
    *   **Запуск / Использование:** Как запустить проект или использовать его основные функции. Укажи команды запуска, порты, переменные окружения если они очевидны из кода.
    *   **Развертывание (если применимо):** Если найдены файлы Docker, CI/CD конфигурации или другие файлы развертывания, опиши процесс деплоя в продакшн.
5.  {instruction}
6.  **Качество:** Текст должен быть понятным, лаконичным и профессиональным. Избегай воды и общих фраз, если нет конкретной информации.
7.  **Тон:** Нейтральный, технический.

**Пожалуйста, сгенерируй README.md на основе этой информации.**
"""
        return prompt.strip()

    def generate_readme_content(
        self,
        ast_data: Dict[str, Any],
        files_content: Dict[str, str],
        style: str = "summary",
        model_key: Optional[SUPPORTED_MODELS] = None,
    ) -> str:
        if not self.openrouter_api_key:
            print("[LlmAgent] OpenRouter API ключ не настроен. Возврат заглушки.")
            return "# Ошибка\n\nAPI ключ для LLM не настроен. Пожалуйста, проверьте конфигурацию."

        current_model_key = model_key or self.default_model_key
        actual_model_name = self.DEFAULT_MODEL_MAPPING.get(current_model_key)

        if not actual_model_name:
            print(
                f"[LlmAgent] Неизвестный ключ модели: {current_model_key}. Используется модель по умолчанию."
            )
            actual_model_name = self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)
            if not actual_model_name:
                return "# Ошибка\n\nНе удалось определить модель LLM для использования."

        print(
            f"[LlmAgent] Генерация README. Стиль: {style}. Модель: {actual_model_name}"
        )

        # Log README generation start
        llm_logger.info(f"📚 Starting README generation")
        llm_logger.info(f"🎨 Style: {style}")
        llm_logger.info(f"🤖 Model: {actual_model_name}")
        llm_logger.info(f"📁 Files to analyze: {len(files_content)}")

        # Log AST data summary
        if ast_data.get("file_details"):
            llm_logger.info(
                f"🔍 AST analysis found {len(ast_data['file_details'])} files with details"
            )

        prompt_text = self._construct_readme_prompt(ast_data, files_content, style)

        # Save prompt to file for debugging
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"logs/llm_prompt_{timestamp}.txt"
        try:
            import os

            os.makedirs("logs", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(
                    f"LLM PROMPT - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n\n")
                f.write(f"Model: {actual_model_name}\n")
                f.write(f"Style: {style}\n")
                f.write(f"Files analyzed: {len(files_content)}\n")
                f.write(f"Prompt length: {len(prompt_text)} characters\n")
                f.write("\n" + "=" * 80 + "\n")
                f.write("FULL PROMPT:\n")
                f.write("=" * 80 + "\n\n")
                f.write(prompt_text)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF PROMPT\n")
                f.write("=" * 80 + "\n")
            llm_logger.info(f"💾 Prompt saved to file: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save prompt to file: {e}")

        # Log enhanced prompt information
        llm_logger.info(
            f"📋 Enhanced prompt includes configuration analysis and project structure"
        )

        # Count configuration files found
        config_files = [
            f
            for f in files_content.keys()
            if any(
                config_type in f.lower()
                for config_type in [
                    "requirements.txt",
                    "pyproject.toml",
                    "package.json",
                    "dockerfile",
                    "docker-compose",
                    "gunicorn.config",
                    ".yml",
                    ".yaml",
                ]
            )
        ]
        if config_files:
            llm_logger.info(
                f"⚙️ Found {len(config_files)} configuration files: {config_files}"
            )

        # Count directories
        directories = set()
        for filepath in files_content.keys():
            parts = filepath.split("/")
            if len(parts) > 1:
                directories.add(parts[0])
        if directories:
            llm_logger.info(
                f"📁 Project has {len(directories)} main directories: {sorted(directories)}"
            )

        readme_markdown = _ask_openrouter_llm(
            prompt=prompt_text,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
            max_tokens=6144,
        )

        # Save LLM response to the same file
        try:
            with open(prompt_filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("LLM RESPONSE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(readme_markdown)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF RESPONSE\n")
                f.write("=" * 80 + "\n")
            llm_logger.info(f"💾 LLM response appended to file: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save LLM response to file: {e}")

        if "⚠️ Ошибка" in readme_markdown:
            print(f"[LlmAgent] Получена ошибка от LLM: {readme_markdown}")
        else:
            print(
                f"[LlmAgent] README успешно сгенерирован моделью {actual_model_name}."
            )

        return readme_markdown

    def generate_folder_documentation(
        self,
        folder_name: str,
        ast_data: Dict[str, Any],
        files_content: Dict[str, str],
        model_key: Optional[SUPPORTED_MODELS] = None,
    ) -> str:
        """
        Generate documentation for a specific folder/module.

        Args:
            folder_name: Name of the folder to document
            ast_data: AST analysis data for files in this folder
            files_content: Content of files in this folder
            model_key: LLM model to use

        Returns:
            Markdown documentation for the folder
        """
        if not self.openrouter_api_key:
            print("[LlmAgent] OpenRouter API ключ не настроен. Возврат заглушки.")
            return "# Ошибка\n\nAPI ключ для LLM не настроен."

        current_model_key = model_key or self.default_model_key
        actual_model_name = self.DEFAULT_MODEL_MAPPING.get(current_model_key)

        if not actual_model_name:
            print(f"[LlmAgent] Неизвестный ключ модели: {current_model_key}.")
            actual_model_name = self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)
            if not actual_model_name:
                return "# Ошибка\n\nНе удалось определить модель LLM."

        llm_logger.info(f"📁 Generating documentation for folder: {folder_name}")
        llm_logger.info(f"🤖 Model: {actual_model_name}")
        llm_logger.info(f"📄 Files in folder: {len(files_content)}")

        # Analyze folder structure
        folder_structure = "Структура папки:\n"
        for filepath in sorted(files_content.keys()):
            relative_path = (
                filepath.replace(f"{folder_name}/", "")
                if folder_name != "root"
                else filepath
            )
            folder_structure += f"- `{relative_path}`\n"

        # Analyze folder components
        folder_components = "Компоненты папки:\n"
        if ast_data.get("file_details"):
            for filepath, details in ast_data["file_details"].items():
                folder_components += (
                    f"\n**{filepath}** ({details.get('type', 'unknown')}):\n"
                )

                if "classes" in details and details["classes"]:
                    folder_components += "- Классы:\n"
                    for cls in details["classes"][:5]:  # Limit to 5 classes
                        folder_components += f"  - `{cls['name']}`: {cls.get('docstring', 'Описание отсутствует')[:100]}...\n"

                if "functions" in details and details["functions"]:
                    folder_components += "- Функции:\n"
                    for func in details["functions"][:5]:  # Limit to 5 functions
                        folder_components += f"  - `{func['name']}()`: {func.get('docstring', 'Описание отсутствует')[:100]}...\n"

        # Include file contents (truncated)
        files_content_summary = "\n\nСодержимое файлов:\n"
        for filepath, content in files_content.items():
            max_length = 1500  # Smaller limit for folder docs
            truncated_content = (
                content[:max_length] + "..." if len(content) > max_length else content
            )
            files_content_summary += (
                f"\n--- {filepath} ---\n```\n{truncated_content}\n```\n"
            )

        prompt = f"""
Ты — опытный технический писатель, специализирующийся на создании документации для модулей и компонентов программных проектов.

Твоя задача — создать детальную документацию для папки/модуля "{folder_name}" на основе анализа его содержимого.

**Информация о папке "{folder_name}":**

{folder_structure}

{folder_components}

{files_content_summary}

**Требования к документации:**
1. **Формат:** Строго Markdown
2. **Язык:** Русский
3. **Структура документа:**
   - # {folder_name.title()} (заголовок папки)
   - ## Описание (краткое описание назначения папки/модуля)
   - ## Компоненты (список и описание основных файлов и их функций)
   - ## Основные классы (если есть - описание ключевых классов)
   - ## Основные функции (если есть - описание ключевых функций)
   - ## Зависимости (если очевидны из кода)
   - ## Примеры использования (если можно определить из кода)

**Качество:**
- Будь конкретным и техническим
- Избегай общих фраз
- Сосредоточься на том, что этот модуль делает и как его использовать
- Используй информацию из анализа кода

**Создай документацию для папки "{folder_name}":**
"""

        # Save prompt for debugging
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"logs/llm_folder_prompt_{folder_name}_{timestamp}.txt"
        try:
            os.makedirs("logs", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write(f"FOLDER DOCUMENTATION PROMPT - {folder_name}\n")
                f.write("=" * 80 + "\n\n")
                f.write(prompt)
            llm_logger.info(f"💾 Folder prompt saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save folder prompt: {e}")

        folder_doc = _ask_openrouter_llm(
            prompt=prompt,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
            max_tokens=4096,
        )

        # Save response
        try:
            with open(prompt_filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("LLM RESPONSE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(folder_doc)
            llm_logger.info(f"💾 Folder response saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save folder response: {e}")

        if "⚠️ Ошибка" in folder_doc:
            print(
                f"[LlmAgent] Ошибка при генерации документации папки {folder_name}: {folder_doc}"
            )
        else:
            print(
                f"[LlmAgent] Документация для папки {folder_name} успешно сгенерирована."
            )

        return folder_doc

    def generate_main_docs_readme(
        self,
        folders: List[str],
        ast_data: Dict[str, Any],
        model_key: Optional[SUPPORTED_MODELS] = None,
    ) -> str:
        """
        Generate main README.md for the docs folder that links to all folder documentation.

        Args:
            folders: List of folder names that have documentation
            ast_data: AST analysis data for the entire project
            model_key: LLM model to use

        Returns:
            Main README.md content for docs folder
        """
        if not self.openrouter_api_key:
            print("[LlmAgent] OpenRouter API ключ не настроен. Возврат заглушки.")
            return "# Ошибка\n\nAPI ключ для LLM не настроен."

        current_model_key = model_key or self.default_model_key
        actual_model_name = self.DEFAULT_MODEL_MAPPING.get(current_model_key)

        if not actual_model_name:
            actual_model_name = self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)
            if not actual_model_name:
                return "# Ошибка\n\nНе удалось определить модель LLM."
        llm_logger.info(f"📚 Generating main docs README")
        llm_logger.info(f"🤖 Model: {actual_model_name}")
        llm_logger.info(f"📁 Folders to document: {len(folders)}")

        # Create folder list with descriptions
        folders_list = "Структура документации:\n"
        for folder in sorted(folders):
            if folder == "root":
                folders_list += (
                    f"- [`{folder}.md`](./{folder}.md) - Файлы в корне проекта\n"
                )
            else:
                folders_list += f"- [`{folder}.md`](./{folder}.md) - Модуль {folder}\n"

        # Project overview from AST
        project_overview = "Обзор проекта:\n"
        if ast_data.get("repository_overview"):
            project_overview += ast_data["repository_overview"] + "\n"

        if ast_data.get("file_details"):
            total_files = len(ast_data["file_details"])
            total_classes = sum(
                len(details.get("classes", []))
                for details in ast_data["file_details"].values()
            )
            total_functions = sum(
                len(details.get("functions", []))
                for details in ast_data["file_details"].values()
            )

            project_overview += f"\n**Статистика проекта:**\n"
            project_overview += f"- Всего файлов: {total_files}\n"
            project_overview += f"- Всего классов: {total_classes}\n"
            project_overview += f"- Всего функций: {total_functions}\n"

        prompt = f"""
Ты — опытный технический писатель, создающий главную страницу документации для проекта.

Твоя задача — создать главный README.md файл для папки docs, который будет служить навигацией по всей документации проекта.

**Информация о проекте:**
{project_overview}

**Доступная документация:**
{folders_list}

**Требования к главному README.md:**
1. **Формат:** Строго Markdown
2. **Язык:** Русский
3. **Структура документа:**
   - # Документация проекта
   - ## О проекте (краткое описание проекта и его назначения)
   - ## Структура документации (навигация по модулям с описанием каждого)
   - ## Быстрый старт (как начать работу с проектом)
   - ## Архитектура (общая схема проекта и взаимодействие модулей)

**Особенности:**
- Сделай документацию дружелюбной для новых разработчиков
- Включи ссылки на соответствующие .md файлы модулей
- Объясни общую архитектуру и принципы организации кода
- Добавь рекомендации по изучению проекта (с чего начать)

**Создай главную страницу документации:**
"""

        # Save prompt for debugging
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"logs/llm_main_docs_prompt_{timestamp}.txt"
        try:
            os.makedirs("logs", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write("MAIN DOCS README PROMPT\n")
                f.write("=" * 80 + "\n\n")
                f.write(prompt)
            llm_logger.info(f"💾 Main docs prompt saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save main docs prompt: {e}")

        main_readme = _ask_openrouter_llm(
            prompt=prompt,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
            max_tokens=5048,
        )

        # Save response
        try:
            with open(prompt_filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("LLM RESPONSE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(main_readme)
            llm_logger.info(f"💾 Main docs response saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save main docs response: {e}")

        if "⚠️ Ошибка" in main_readme:
            print(f"[LlmAgent] Ошибка при генерации главного README: {main_readme}")
        else:
            print("[LlmAgent] Главный README для docs успешно сгенерирован.")

        return main_readme

    def update_folder_documentation(
        self,
        folder_name: str,
        recent_prs: List[Dict[str, Any]],
        ast_data: Dict[str, Any],
        files_content: Dict[str, str],
        model_key: Optional[SUPPORTED_MODELS] = None,
    ) -> str:
        """
        Update documentation for a specific folder based on recent changes.

        Args:
            folder_name: Name of the folder to update documentation for
            recent_prs: List of recent merged pull requests
            ast_data: AST analysis data for files in this folder
            files_content: Content of files in this folder
            model_key: LLM model to use

        Returns:
            Updated markdown documentation for the folder
        """
        if not self.openrouter_api_key:
            print("[LlmAgent] OpenRouter API ключ не настроен. Возврат заглушки.")
            return "# Ошибка\n\nAPI ключ для LLM не настроен."

        current_model_key = model_key or self.default_model_key
        actual_model_name = self.DEFAULT_MODEL_MAPPING.get(current_model_key)

        if not actual_model_name:
            actual_model_name = self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)
            if not actual_model_name:
                return "# Ошибка\n\nНе удалось определить модель LLM."

        llm_logger.info(f"🔄 Updating documentation for folder: {folder_name}")
        llm_logger.info(f"🤖 Model: {actual_model_name}")
        llm_logger.info(f"📋 Recent PRs to analyze: {len(recent_prs)}")

        # Analyze recent changes related to this folder
        folder_related_changes = []
        for pr in recent_prs:
            folder_files = [
                file_info
                for file_info in pr.get("files_changed", [])
                if file_info["filename"].startswith(f"{folder_name}/")
                or (folder_name == "root" and "/" not in file_info["filename"])
            ]
            if folder_files:
                folder_related_changes.append({"pr": pr, "files": folder_files})

        # Construct PR summary for this folder
        pr_summary = f"Изменения в папке {folder_name} (из последних PR):\n"
        if folder_related_changes:
            for change in folder_related_changes[:3]:  # Limit to 3 most recent
                pr = change["pr"]
                pr_summary += f"\n**PR #{pr['number']}: {pr['title']}**\n"
                pr_summary += f"- Дата: {pr['merged_at']}\n"
                if pr["body"]:
                    body_preview = (
                        pr["body"][:200] + "..."
                        if len(pr["body"]) > 200
                        else pr["body"]
                    )
                    pr_summary += f"- Описание: {body_preview}\n"
                pr_summary += f"- Измененные файлы в {folder_name}:\n"
                for file_info in change["files"]:
                    pr_summary += f"  - {file_info['filename']} ({file_info['status']}, +{file_info['additions']}/-{file_info['deletions']})\n"
        else:
            pr_summary += f"Нет изменений в папке {folder_name} в последних PR.\n"

        # Current folder structure
        current_structure = f"Текущая структура папки {folder_name}:\n"
        for filepath in sorted(files_content.keys()):
            current_structure += f"- `{filepath}`\n"

        # Current components analysis
        current_components = f"Текущие компоненты папки {folder_name}:\n"
        if ast_data.get("file_details"):
            for filepath, details in ast_data["file_details"].items():
                current_components += f"\n**{filepath}**:\n"
                if "classes" in details and details["classes"]:
                    class_names = [cls["name"] for cls in details["classes"]]
                    current_components += f"- Классы: {', '.join(class_names)}\n"
                if "functions" in details and details["functions"]:
                    func_names = [func["name"] for func in details["functions"]]
                    current_components += f"- Функции: {', '.join(func_names)}\n"

        prompt = f"""
Ты — опытный технический писатель, специализирующийся на поддержании актуальной документации для модулей программных проектов.

Твоя задача — обновить документацию для папки/модуля "{folder_name}" на основе последних изменений в проекте.

**ВАЖНО:** Создай новую актуальную документацию, учитывая последние изменения. Если изменений в этой папке не было, создай документацию на основе текущего состояния.

**Анализ изменений:**
{pr_summary}

**Текущее состояние папки:**
{current_structure}

{current_components}

**Требования к обновленной документации:**
1. **Формат:** Строго Markdown
2. **Язык:** Русский
3. **Структура документа:**
   - # {folder_name.title()}
   - ## Описание (что делает этот модуль/папка)
   - ## Последние изменения (если были значимые изменения)
   - ## Компоненты (файлы и их назначение)
   - ## Основные классы и функции
   - ## Примеры использования (если применимо)

**Подход к обновлению:**
- Учти все изменения из PR, которые касаются этой папки
- Обнови описания компонентов, если они изменились
- Добавь информацию о новых файлах или функциях
- Убери информацию об удаленных компонентах
- Обнови примеры использования, если API изменился

**Создай обновленную документацию для папки "{folder_name}":**
"""

        # Save prompt for debugging
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"logs/llm_update_folder_prompt_{folder_name}_{timestamp}.txt"
        try:
            os.makedirs("logs", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write(f"UPDATE FOLDER DOCUMENTATION PROMPT - {folder_name}\n")
                f.write("=" * 80 + "\n\n")
                f.write(prompt)
            llm_logger.info(f"💾 Update folder prompt saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save update folder prompt: {e}")

        updated_folder_doc = _ask_openrouter_llm(
            prompt=prompt,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
        )

        # Save response
        try:
            with open(prompt_filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("LLM RESPONSE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(updated_folder_doc)
            llm_logger.info(f"💾 Update folder response saved: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save update folder response: {e}")

        if "⚠️ Ошибка" in updated_folder_doc:
            print(
                f"[LlmAgent] Ошибка при обновлении документации папки {folder_name}: {updated_folder_doc}"
            )
        else:
            print(f"[LlmAgent] Документация папки {folder_name} успешно обновлена.")

        return updated_folder_doc

    def update_readme_content(
        self,
        existing_readme: str,
        recent_prs: List[Dict[str, Any]],
        ast_data: Dict[str, Any],
        files_content: Dict[str, str],
        style: str = "summary",
        model_key: Optional[SUPPORTED_MODELS] = None,
    ) -> str:
        """
        Update existing README content based on recent merged PRs and current project state.
        Args:
            existing_readme: Current README content
            recent_prs: List of recent merged pull requests
            ast_data: AST analysis data
            files_content: Current repository files content
            style: Documentation style ("summary" or "detailed")
            model_key: LLM model to use
        Returns:
            Updated README content as markdown string
        """
        if not self.openrouter_api_key:
            print("[LlmAgent] OpenRouter API ключ не настроен. Возврат заглушки.")
            return "# Ошибка\n\nAPI ключ для LLM не настроен. Пожалуйста, проверьте конфигурацию."

        current_model_key = model_key or self.default_model_key
        actual_model_name = self.DEFAULT_MODEL_MAPPING.get(current_model_key)

        if not actual_model_name:
            print(
                f"[LlmAgent] Неизвестный ключ модели: {current_model_key}. Используется модель по умолчанию."
            )
            actual_model_name = self.DEFAULT_MODEL_MAPPING.get(self.default_model_key)
            if not actual_model_name:
                return "# Ошибка\n\nНе удалось определить модель LLM для использования."

        print(
            f"[LlmAgent] Обновление README. Стиль: {style}. Модель: {actual_model_name}"
        )

        # Log README update start
        llm_logger.info(f"🔄 Starting README update")
        llm_logger.info(f"🎨 Style: {style}")
        llm_logger.info(f"🤖 Model: {actual_model_name}")
        llm_logger.info(f"📋 Recent PRs to analyze: {len(recent_prs)}")
        llm_logger.info(f"📁 Files to analyze: {len(files_content)}")

        # Construct PR summary
        pr_summary = "Последние изменения в репозитории (merged PR):\n"
        if recent_prs:
            for pr in recent_prs[:5]:  # Limit to 5 most recent PRs
                pr_summary += f"\n**PR #{pr['number']}: {pr['title']}**\n"
                pr_summary += f"- Автор: {pr['user']}\n"
                pr_summary += f"- Дата слияния: {pr['merged_at']}\n"
                if pr["body"]:
                    # Limit PR body length
                    body_preview = (
                        pr["body"][:300] + "..."
                        if len(pr["body"]) > 300
                        else pr["body"]
                    )
                    pr_summary += f"- Описание: {body_preview}\n"
                if pr["files_changed"]:
                    pr_summary += f"- Измененные файлы ({len(pr['files_changed'])}):\n"
                    for file_info in pr["files_changed"][
                        :10
                    ]:  # Limit to 10 files per PR
                        pr_summary += f"  - {file_info['filename']} ({file_info['status']}, +{file_info['additions']}/-{file_info['deletions']})\n"
        else:
            pr_summary += "Нет недавних merged PR для анализа.\n"

        # Get current project structure summary
        project_structure_summary = "Текущая структура проекта:\n"
        if ast_data.get("file_details"):
            for filepath, details in list(ast_data["file_details"].items())[:10]:
                project_structure_summary += (
                    f"- Файл `{filepath}` ({details.get('type', 'unknown')}):\n"
                )
                if "functions" in details and details["functions"]:
                    func_names = [f"`{f['name']}()`" for f in details["functions"][:3]]
                    project_structure_summary += (
                        f"  - Функции: {', '.join(func_names)}\n"
                    )
                if "classes" in details and details["classes"]:
                    class_names = [f"`{c['name']}`" for c in details["classes"][:2]]
                    project_structure_summary += (
                        f"  - Классы: {', '.join(class_names)}\n"
                    )

        # Construct update prompt
        prompt = f"""
        Ты — опытный технический писатель и разработчик, специализирующийся на поддержании актуальной документации для программных проектов.
        Твоя задача — проанализировать существующий README.md файл и обновить его на основе последних изменений в проекте, если это необходимо.

        **ВАЖНО:** Обновляй документацию ТОЛЬКО если есть существенные изменения, которые влияют на:
        - Функциональность проекта
        - Способы установки или запуска
        - Архитектуру или структуру проекта
        - Новые возможности или компоненты
        - Изменения в API или интерфейсах

        Если изменения незначительные (исправления багов, рефакторинг без изменения функциональности, обновления зависимостей), то верни существующий README без изменений.

        **Существующий README.md:**
        ```markdown
        {existing_readme}
        Анализ последних изменений:
        {pr_summary}

        Текущее состояние проекта:
        {project_structure_summary}

        Инструкции по обновлению:

        Язык: Русский
        Формат: Строго Markdown
        Подход: Сохрани структуру и стиль существующего README
        Обновления: Внеси изменения только там, где это действительно необходимо
        Качество: Поддерживай профессиональный тон и ясность изложения
        Что нужно проверить и обновить при необходимости:

        Описание проекта (если добавлены новые основные функции)
        Список возможностей (если добавлены новые фичи)
        Инструкции по установке (если изменились зависимости или процесс установки)
        Примеры использования (если изменился API или добавлены новые способы использования)
        Структура проекта (если добавлены новые важные директории или файлы)
        Технологический стек (если добавлены новые технологии)
        Если обновления не требуются, верни точно такой же README без изменений.
        Если обновления необходимы, верни обновленную версию README.md:
        """

        # Save prompt to file for debugging
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"logs/llm_update_prompt_{timestamp}.txt"
        try:
            import os

            os.makedirs("logs", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(
                    f"LLM UPDATE PROMPT - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n\n")
                f.write(f"Model: {actual_model_name}\n")
                f.write(f"Style: {style}\n")
                f.write(f"Recent PRs: {len(recent_prs)}\n")
                f.write(f"Files analyzed: {len(files_content)}\n")
                f.write(f"Prompt length: {len(prompt)} characters\n")
                f.write("\n" + "=" * 80 + "\n")
                f.write("FULL PROMPT:\n")
                f.write("=" * 80 + "\n\n")
                f.write(prompt)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF PROMPT\n")
                f.write("=" * 80 + "\n")
                llm_logger.info(f"💾 Update prompt saved to file: {prompt_filename}")
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save update prompt to file: {e}")

        updated_readme = _ask_openrouter_llm(
            prompt=prompt,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
        )

        # Save LLM response to the same file
        try:
            with open(prompt_filename, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("LLM RESPONSE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(updated_readme)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("END OF RESPONSE\n")
                f.write("=" * 80 + "\n")
                llm_logger.info(
                    f"💾 LLM update response appended to file: {prompt_filename}"
                )
        except Exception as e:
            llm_logger.warning(f"⚠️ Failed to save LLM update response to file: {e}")

        if "⚠️ Ошибка" in updated_readme:
            print(f"[LlmAgent] Получена ошибка от LLM при обновлении: {updated_readme}")
        else:
            print(f"[LlmAgent] README успешно обновлен моделью {actual_model_name}.")

        return updated_readme

