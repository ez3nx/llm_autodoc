# LLM AutoDoc: Автоматическая генерация документации

LLM AutoDoc — инструмент для автоматической генерации документации для репозиториев кода с использованием больших языковых моделей (LLM).  Он анализирует структуру проекта,  читает файлы кода и генерирует  README файл, содержащий краткое описание проекта, его компонентов и инструкций по использованию.

## 🚀 Возможности

* Автоматический анализ структуры проекта с помощью анализатора абстрактного синтаксического дерева (AST).
* Генерация README файла, содержащего описание проекта, его компонентов и инструкций по использованию.
* Поддержка различных стилей генерации документации (например, краткое описание или подробное руководство).
* Использование LLM для генерации более качественного и информативного текста.
* CLI интерфейс для удобного запуска.
* Python API для интеграции в другие приложения.


## 📦 Установка

1. **Клонирование репозитория:**
   ```bash
   git clone https://github.com/yourusername/llm_autodoc.git
   ```
2. **Установка зависимостей:**
   ```bash
   cd llm_autodoc
   pip install -r requirements.txt
   ```
3. **(Опционально) Установка в режиме разработки:** Для внесения изменений в код и тестирования:
   ```bash
   pip install -e .
   ```

## 🔧 Быстрый старт

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта и добавьте следующие переменные:

```
OPENROUTER_API_KEY=ваш_openrouter_api_ключ
GITHUB_TOKEN=ваш_github_токен  #(Необязательно, для доступа к удаленным репозиториям)
```

### 2. Генерация документации

Для генерации документации для текущей директории используйте команду:

```bash
llm-autodoc generate .
```

Для указания выходного файла:

```bash
llm-autodoc generate . --output my_readme.md
```

Для выбора модели LLM (например, `claude-sonnet`) и стиля документации (например, `detailed`):

```bash
llm-autodoc generate . --model claude-sonnet --style detailed
```

### 3. Использование Python API

```python
from llm_autodoc.services import AstAnalyzer, GitHubParser, LlmAgent

# Инициализация сервисов
llm_agent = LlmAgent(openrouter_api_key="ваш_openrouter_api_ключ")
github_parser = GitHubParser(github_token="ваш_github_токен") # Необязательно
ast_analyzer = AstAnalyzer()

# Анализ репозитория
ast_data = ast_analyzer.analyze_directory(".")
files_content = github_parser.parse_local_repository(".")

# Генерация документации
readme_content = llm_agent.generate_readme_content(ast_data=ast_data, files_content=files_content, style="summary")
print(readme_content)

# Сохранение в файл:
with open("README.md", "w") as f:
    f.write(readme_content)
```

## 📁 Структура проекта

```
llm_autodoc/
├── cli.py          # CLI интерфейс
├── services/       # Сервисы для анализа кода и генерации документации
│   ├── __init__.py
│   ├── ast_analyzer.py
│   ├── doc_generator.py
│   ├── github_parser.py
│   └── llm_agent.py
├── templates/      # Шаблоны для README
│   └── readme_template.md
└── __init__.py
test_project/
├── example.py      # Примерный проект для тестирования
└── utils.py        # Вспомогательные функции
```

## 🛠️ Технологический стек

* Python 3.8+
* OpenRouter API (для доступа к LLM)
* GitHub API (опционально, для доступа к удаленным репозиториям)
* Jinja2 (для рендеринга шаблонов)
* networkx (для анализа зависимостей - возможно, в будущих версиях)


## 🤝 Вклад

Приглашаем к участию в развитии проекта!


## 📄 Лицензия

MIT License.


