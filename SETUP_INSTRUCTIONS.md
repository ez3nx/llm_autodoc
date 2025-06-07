# Инструкции по настройке LLM AutoDoc CI/CD

## 🚀 Быстрый старт

### 1. Установка библиотеки

```bash
# Установка из PyPI (когда будет опубликована)
pip install llm-autodoc

# Или установка из исходников
git clone https://github.com/yourusername/llm_autodoc.git
cd llm_autodoc
pip install -e .
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# OpenRouter API ключ для доступа к LLM
OPENROUTER_API_KEY=your_openrouter_api_key_here

# GitHub токен для доступа к репозиториям
GITHUB_TOKEN=your_github_token_here
```

### 3. Использование CLI

```bash
# Генерация документации для текущего репозитория
llm-autodoc generate .

# Генерация с указанием модели и стиля
llm-autodoc generate . --model claude-sonnet --style detailed

# Обновление существующей документации
llm-autodoc update . --readme README.md
```

## 🔧 Настройка CI/CD

### GitHub Actions Secrets

Добавьте следующие секреты в настройки вашего GitHub репозитория:

1. **OPENROUTER_API_KEY** - ваш API ключ от OpenRouter
2. **PYPI_API_TOKEN** - токен для публикации в PyPI (опционально)
3. **TEST_PYPI_API_TOKEN** - токен для тестовой публикации (опционально)

### Автоматическая генерация документации

Workflow `.github/workflows/auto-docs.yml` автоматически:

- ✅ Запускается при создании/обновлении Pull Request
- ✅ Анализирует изменения в коде
- ✅ Генерирует обновленную документацию
- ✅ Создает коммит с обновленным README.md
- ✅ Добавляет комментарий к PR с описанием изменений
- ✅ Создает автоматический код-ревью

### Настройка для других CI/CD систем

#### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - docs

auto-docs:
  stage: docs
  image: python:3.11
  script:
    - pip install llm-autodoc
    - llm-autodoc generate . --output README.md
    - |
      if [ -n "$(git diff --name-only)" ]; then
        git config --global user.email "gitlab-ci@example.com"
        git config --global user.name "GitLab CI"
        git add README.md
        git commit -m "docs: auto-update README.md"
        git push origin HEAD:$CI_COMMIT_REF_NAME
      fi
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    GITHUB_TOKEN: $GITHUB_TOKEN
  only:
    - merge_requests
```

#### Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        OPENROUTER_API_KEY = credentials('openrouter-api-key')
        GITHUB_TOKEN = credentials('github-token')
    }
    
    stages {
        stage('Generate Docs') {
            steps {
                sh 'pip install llm-autodoc'
                sh 'llm-autodoc generate . --output README.md'
                
                script {
                    if (sh(script: 'git diff --name-only', returnStdout: true).trim()) {
                        sh '''
                            git config user.email "jenkins@example.com"
                            git config user.name "Jenkins"
                            git add README.md
                            git commit -m "docs: auto-update README.md"
                            git push origin HEAD
                        '''
                    }
                }
            }
        }
    }
    
    triggers {
        pollSCM('H/5 * * * *')
    }
}
```

## 🔑 Получение API ключей

### OpenRouter API Key

1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Перейдите в раздел API Keys
3. Создайте новый ключ
4. Скопируйте ключ и добавьте в переменные окружения

### GitHub Token

1. Перейдите в GitHub Settings → Developer settings → Personal access tokens
2. Создайте новый token с правами:
   - `repo` (для доступа к приватным репозиториям)
   - `public_repo` (для публичных репозиториев)
   - `read:org` (для организационных репозиториев)
3. Скопируйте токен и добавьте в переменные окружения

## 📊 Мониторинг и логирование

### Просмотр логов GitHub Actions

1. Перейдите в раздел Actions вашего репозитория
2. Выберите workflow "Auto Documentation Update"
3. Просмотрите детальные логи каждого шага

### Локальная отладка

```bash
# Включение подробного логирования
export LOG_LEVEL=DEBUG
llm-autodoc generate . --model gemini-flash --style summary

# Проверка конфигурации
python -c "
import os
from llm_autodoc import LlmAgent
agent = LlmAgent()
print('OpenRouter key:', 'OK' if agent.openrouter_api_key else 'MISSING')
"
```

## 🛠️ Кастомизация

### Создание собственных шаблонов

1. Создайте директорию `templates` в вашем проекте
2. Скопируйте базовый шаблон из `llm_autodoc/templates/readme_template.md`
3. Модифицируйте под ваши нужды
4. Используйте кастомный шаблон:

```python
from llm_autodoc import DocGenerator

doc_gen = DocGenerator(template_dir="./templates")
readme = doc_gen.render_readme("my_template.md", context_data)
```

### Настройка стилей документации

Доступные стили:
- `summary` - краткое описание (по умолчанию)
- `detailed` - подробная документация
- `technical` - техническая документация с деталями API

### Выбор LLM модели

Поддерживаемые модели:
- `gemini-flash` - быстрая и экономичная (по умолчанию)
- `claude-sonnet` - высокое качество текста
- `gpt-4o-mini` - сбалансированный вариант

## 🔍 Устранение неполадок

### Частые проблемы

1. **Ошибка API ключа**
   ```
   ❌ Ошибка OpenRouter: API ключ не предоставлен
   ```
   Решение: Проверьте переменную окружения `OPENROUTER_API_KEY`

2. **Ошибка доступа к репозиторию**
   ```
   ❌ Ошибка доступа к GitHub API
   ```
   Решение: Проверьте `GITHUB_TOKEN` и права доступа

3. **Workflow не запускается**
   - Проверьте настройки Actions в репозитории
   - Убедитесь, что workflow файл находится в `.github/workflows/`
   - Проверьте синтаксис YAML файла

### Получение поддержки

- 📝 Создайте Issue в репозитории проекта
- 💬 Обратитесь к документации API
- 🔍 Проверьте существующие Issues на похожие проблемы

## 📈 Расширенные возможности

### Интеграция с другими инструментами

- **Pre-commit hooks** - автоматическое обновление документации перед коммитом
- **Slack/Discord уведомления** - оповещения об обновлении документации
- **Confluence/Notion** - синхронизация с внешними системами документации

### Планы развития

- 🔄 Поддержка других языков программирования
- 📊 Генерация диаграмм и схем архитектуры
- 🌐 Мультиязычная документация
- 📱 Интеграция с мобильными приложениями 