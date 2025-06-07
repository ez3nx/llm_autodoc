# app/services/llm_agent.py
import os
import requests
from typing import Dict, Any, Optional, Literal
from dotenv import load_dotenv

# Загрузка переменных окружения, если файл запускается отдельно
# В основном приложении Streamlit это обычно делается в ui.py
# Этот блок if __name__ == "__main__": с load_dotenv был здесь,
# но так как ui.py уже делает load_dotenv(), и этот файл теперь
# будет использоваться только как модуль, явная загрузка здесь не нужна,
# если только для независимого тестирования вне Streamlit-контекста,
# но тестовый блок ниже мы удаляем.

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
        # "HTTP-Referer": "YOUR_SITE_URL", # Рекомендуется для OpenRouter
        # "X-Title": "Your App Name",     # Рекомендуется для OpenRouter
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=180
        )
        response.raise_for_status()
        response_json = response.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            content = response_json["choices"][0].get("message", {}).get("content")
            if content:
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
    SUPPORTED_MODELS = Literal[
        "qwen-coder",
        "gemini-flash",
        "gpt-3.5-turbo",
    ]
    DEFAULT_MODEL_MAPPING = {
        "qwen-coder": "qwen/qwen-2.5-coder-32b-instruct",
        "gemini-flash": "google/gemini-flash-1.5",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
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
                    func_names = [
                        f"`{f['name']}()`" for f in details["functions"][:3]
                    ]
                    project_structure_summary += (
                        f"  - Функции: {', '.join(func_names)}\n"
                    )
                if "classes" in details and details["classes"]:
                    class_names = [
                        f"`{c['name']}`" for c in details["classes"][:2]
                    ]
                    project_structure_summary += (
                        f"  - Классы: {', '.join(class_names)}\n"
                    )
        else:
            project_structure_summary = (
                "Детальный анализ структуры файлов не представлен."
            )

        contextual_code_snippets = "\n\nНекоторые ключевые файлы для контекста:\n"
        snippet_count = 0
        for filepath, content in list(files_content.items()):
            if filepath.lower().endswith((".py", ".go", ".ts", ".js")) and (
                "main." in filepath.lower()
                or "app." in filepath.lower()
                or "server." in filepath.lower()
                or "index." in filepath.lower()
            ):
                if (
                    len(content) < 2000 and snippet_count < 3
                ):
                    contextual_code_snippets += f"--- {filepath} ---\n```\n{content[:1000]}...\n```\n\n"
                    snippet_count += 1
        if snippet_count == 0:
            contextual_code_snippets = ""

        readme_style_instruction = "подробное описание каждого компонента, его назначения, параметров и возвращаемых значений (если применимо)."
        if style == "summary":
            readme_style_instruction = "краткое изложение основных функций и назначения проекта, без излишней детализации."

        prompt = f"""
Ты — опытный технический писатель и разработчик, специализирующийся на создании качественной документации для программных проектов.
Твоя задача — сгенерировать информативный и хорошо структурированный README.md файл для проекта на основе предоставленной информации о его структуре и содержимом некоторых файлов.

**Информация о проекте:**
{ast_data.get("repository_overview", "Обзор проекта не предоставлен.")}

**Анализ структуры кода (из AST):**
{project_structure_summary}
{contextual_code_snippets}

**Требования к README.md:**
1.  **Формат:** Строго Markdown.
2.  **Язык:** Русский.
3.  **Стиль документации:** {readme_style_instruction}
4.  **Обязательные разделы (если информация доступна):**
    *   **Название проекта** (придумай подходящее, если не очевидно из данных).
    *   **Описание проекта:** Краткое описание (1-3 предложения) того, что делает проект.
    *   **Основные возможности / Ключевые компоненты:** Опиши основные части проекта, их назначение. Используй данные из анализа структуры кода.
    *   **Технологический стек:** Попробуй определить или предположить основные технологии/языки, используемые в проекте, на основе расширений файлов и импортов.
    *   **Установка (предположительно):** Предоставь общие шаги для установки (например, клонирование, установка зависимостей).
    *   **Запуск / Использование (предположительно):** Как запустить проект или использовать его основные функции.
    *   **(Опционально) Структура проекта:** Если это уместно для выбранного стиля, кратко опиши структуру директорий и файлов.
5.  **Качество:** Текст должен быть понятным, лаконичным и профессиональным. Избегай воды и общих фраз, если нет конкретной информации.
6.  **Тон:** Нейтральный, технический.

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
        prompt_text = self._construct_readme_prompt(ast_data, files_content, style)
        
        readme_markdown = _ask_openrouter_llm(
            prompt=prompt_text,
            model_name=actual_model_name,
            api_key=self.openrouter_api_key,
        )

        if "⚠️ Ошибка" in readme_markdown:
            print(f"[LlmAgent] Получена ошибка от LLM: {readme_markdown}")
        else:
            print(
                f"[LlmAgent] README успешно сгенерирован моделью {actual_model_name}."
            )
        return readme_markdown