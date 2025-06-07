# LLM AutoDoc: Автоматическая генерация документации для репозиториев кода

LLM AutoDoc — инструмент для автоматической генерации документации для проектов на основе анализа кода и использования больших языковых моделей (LLM).  Он анализирует структуру проекта,  читает файлы кода и генерирует  README файл, содержащий краткое описание проекта, его компонентов и инструкций по использованию.  Проект включает в себя CLI инструмент и Python API для гибкого использования.

## 🚀 Возможности

* Автоматический анализ структуры проекта и файлов с помощью анализатора абстрактного синтаксического дерева (AST).
* Генерация README файла, содержащего описание проекта, его компонентов, инструкций по использованию и примеров кода.
* Поддержка различных стилей генерации документации (например, краткое описание или подробное руководство).
* Использование LLM (через OpenRouter) для генерации более качественного и информативного текста.
* CLI интерфейс (`llm-autodoc`) для удобного запуска.
* Python API для интеграции в другие приложения.
* Поддержка GitHub интеграции для автоматического обновления документации.


## 📦 Установка

1. **Клонирование репозитория:**
   ```bash
   git clone https://github.com/yourusername/llm_autodoc.git
   ```
2. **Установка зависимостей:**
   ```bash
   cd llm_autodoc
   pip install -r requirements.txt  # Или pip install -e . для разработки
   ```

## 🔧 Быстрый старт

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта и добавьте следующие переменные:

```
OPENROUTER_API_KEY=ваш_openrouter_api_ключ
GITHUB_TOKEN=ваш_github_токен  #(Необязательно, для доступа к удаленным репозиториям)
```

### 2. Генерация документации (CLI)

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
github_parser = GitHubParser(github_token="ваш_github_токен") # Опционально
ast_analyzer = AstAnalyzer()

# Анализ репозитория
ast_data = ast_analyzer.analyze_directory(".")
files_content = github_parser.parse_local_repository(".")

# Генерация документации
readme_content = llm_agent.generate_readme_content(
    ast_data=ast_data,
    files_content=files_content,
    style="summary"
)
print(readme_content) # Вывод сгенерированного README
```

## 📁 Структура проекта

```
llm_autodoc/
├── services/
│   ├── ast_analyzer.py
│   ├── doc_generator.py
│   ├── github_parser.py
│   ├── llm_agent.py
│   └── __init__.py
├── cli.py
├── __init__.py
└── templates/
    └── readme_template.md
test_project/
├── utils.py
└── README.md
```

`llm_autodoc` содержит основной функционал генерации документации.  `test_project` - пример проекта для демонстрации.


## 🤝 Contributing

Вклад приветствуется!  Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) (файл будет создан позже).


## 📄 Лицензия

MIT License.


##  Пример проекта (test_project)

Этот репозиторий содержит пример проекта `test_project`, демонстрирующий возможности LLM AutoDoc.  Он включает в себя несколько утилитных функций и служит для тестирования генерации документации.  Более подробное описание находится в `test_project/README.md`.


##  GitHub Actions

Включен workflow для автоматической генерации документации при каждом push в репозиторий.  См. `.github/workflows/auto-docs.yml`.  Для работы workflow необходимы секреты `OPENROUTER_API_KEY` и (опционально) `GITHUB_TOKEN`.


