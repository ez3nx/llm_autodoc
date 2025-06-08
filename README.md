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

### Способ 1: Установка из GitHub (рекомендуемый)

```bash
# Установка последней версии
pip install git+https://github.com/ez3nx/llm_autodoc.git

# Установка конкретной ветки
pip install git+https://github.com/ez3nx/llm_autodoc.git@feature/ci-cd
```

### Способ 2: Установка для разработки

```bash
# Клонирование репозитория
git clone https://github.com/ez3nx/llm_autodoc.git
cd llm_autodoc

# Установка в режиме разработки
pip install -e .
```

### Способ 3: Установка из PyPI (когда будет опубликовано)

```bash
pip install llm-autodoc
```

## 🔧 Быстрый старт

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта и добавьте следующие переменные:

```bash
OPENROUTER_API_KEY=ваш_openrouter_api_ключ
TOKEN_AUTODOC=ваш_github_токен  # (Опционально, для расширенных прав)
```

Или установите переменные окружения:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
export TOKEN_AUTODOC="your_github_token_here"
```

**Получение API ключей:**
- **OpenRouter API Key**: Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/) и создайте API ключ
- **GitHub Token**: Создайте персональный токен в GitHub Settings → Developer settings → Personal access tokens

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


## 🔄 CI/CD Интеграция

### Настройка автоматической генерации документации в вашем проекте

LLM AutoDoc поддерживает автоматическую генерацию документации через GitHub Actions. При каждом Pull Request документация будет автоматически обновляться.

#### 1. Создание workflow файла

Создайте файл `.github/workflows/auto-docs.yml` в вашем репозитории:

```yaml
name: Auto Documentation Update

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, master, develop]
  workflow_dispatch:

jobs:
  auto-docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
        token: ${{ secrets.GITHUB_TOKEN }}
        ref: ${{ github.head_ref }}
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install llm-autodoc
      run: |
        python -m pip install --upgrade pip
        pip install git+https://github.com/ez3nx/llm_autodoc.git
        
    - name: Generate documentation
      env:
        OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        TOKEN_AUTODOC: ${{ secrets.TOKEN_AUTODOC }}
      run: |
        echo "🚀 Starting automatic documentation generation..."
        llm-autodoc generate . --output README_new.md --model gemini-flash --style summary
        
        if [ -f "README_new.md" ]; then
          if [ -f "README.md" ]; then
            if ! diff -q README.md README_new.md > /dev/null; then
              mv README_new.md README.md
              echo "DOCS_UPDATED=true" >> $GITHUB_ENV
            else
              rm README_new.md
              echo "DOCS_UPDATED=false" >> $GITHUB_ENV
            fi
          else
            mv README_new.md README.md
            echo "DOCS_UPDATED=true" >> $GITHUB_ENV
          fi
        fi
    
    - name: Commit and push changes
      if: env.DOCS_UPDATED == 'true'
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add README.md
        git commit -m "docs: auto-update README.md via LLM AutoDoc"
        
        BRANCH_NAME="${{ github.head_ref }}"
        if [ -n "$BRANCH_NAME" ]; then
          git push origin HEAD:$BRANCH_NAME
        else
          git push
        fi
    
    - name: Comment on PR
      if: env.DOCS_UPDATED == 'true' && github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## 📚 Documentation Auto-Updated
            
            README.md был автоматически обновлен с помощью LLM AutoDoc.
            
            *Обновление выполнено автоматически [LLM AutoDoc](https://github.com/ez3nx/llm_autodoc)*`
          })
```

#### 2. Настройка секретов

1. Перейдите в **Settings** → **Secrets and variables** → **Actions**
2. Добавьте секреты:
   - **`OPENROUTER_API_KEY`** (обязательный) - получите на [OpenRouter](https://openrouter.ai/)
   - **`TOKEN_AUTODOC`** (опциональный) - персональный GitHub токен с правами `repo`

#### 3. Способы запуска

**Автоматический запуск:**
- При создании Pull Request
- При обновлении существующего PR

**Ручной запуск:**
- Перейдите в **Actions** → **Auto Documentation Update**
- Нажмите **Run workflow**

#### 4. Fallback режим

Если `OPENROUTER_API_KEY` не настроен, система работает в fallback режиме:
- Создается базовая документация без LLM
- Анализируется структура проекта
- Генерируется стандартный README

### Пример использования в других проектах

```bash
# Установка в новом проекте
pip install git+https://github.com/ez3nx/llm_autodoc.git

# Локальная генерация
export OPENROUTER_API_KEY="your_api_key"
llm-autodoc generate . --model gemini-flash --style summary

# Проверка результата
cat README.md
```

Подробные инструкции по настройке секретов см. в [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md).


