#!/usr/bin/env python3
import os
import click
from dotenv import load_dotenv

from app.services.github_parser import GithubParser
from app.services.llm_agent import LlmAgent
from app.services.ast_analyzer import AstAnalyzer  # Предположим, что он всё-таки нужен

@click.command()
@click.option('--repo', prompt="🔗 Введите ссылку на GitHub репозиторий", help="URL публичного GitHub-репозитория")
@click.option('--style', default='summary', type=click.Choice(['summary', 'detailed']), help="Стиль README: summary или detailed")
@click.option('--model', default='gemini-flash', type=click.Choice([
    'claude-sonnet', 'gemini-flash', 'gpt-4o-mini'
]), help="Модель LLM")
@click.option('--output', default='README.generated.md', help="Файл вывода")
def generate_readme(repo, style, model, output):
    """⚙️ Генерация README.md с помощью LLM"""

    load_dotenv()

    github_token = os.getenv("GITHUB_TOKEN_AUTODOC")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not github_token or not openrouter_key:
        click.echo("❌ Не хватает переменных окружения. Проверь .env файл.")
        return

    click.echo(f"🚀 Загружаем репозиторий: {repo}")
    parser = GithubParser(github_token)
    files_content = parser.get_repo_files_content(repo_url=repo)

    if not files_content:
        click.echo("⚠️ Не удалось загрузить файлы из репозитория.")
        return

    click.echo(f"📊 Найдено файлов: {len(files_content)}")

    click.echo("🧠 Анализ структуры проекта...")
    analyzer = AstAnalyzer()
    ast_data = analyzer.analyze_repository(files_content)

    click.echo(f"🤖 Генерация документации с помощью LLM ({model}, стиль: {style})...")
    agent = LlmAgent(openrouter_api_key=openrouter_key, default_model=model)
    readme = agent.generate_readme_content(ast_data, files_content, style=style)

    with open(output, "w", encoding="utf-8") as f:
        f.write(readme)

    click.echo(f"✅ README сохранён в файл: {output}")

if __name__ == "__main__":
    generate_readme()
