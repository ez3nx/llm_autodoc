# {{ project_name }}

{{ description }}

## 🚀 Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

## 📦 Installation

```bash
pip install {{ package_name }}
```

## 🔧 Usage

### Command Line Interface

```bash
# Generate documentation for a repository
{{ package_name }} generate /path/to/repo

# Update existing documentation
{{ package_name }} update /path/to/repo
```

### Python API

```python
from {{ package_name }} import LlmAgent, GitHubParser, ASTAnalyzer

# Initialize services
llm_agent = LlmAgent(openrouter_api_key="your-key")
github_parser = GitHubParser(github_token="your-token")
ast_analyzer = ASTAnalyzer()

# Analyze repository
ast_data = ast_analyzer.analyze_directory("/path/to/repo")
files_content = github_parser.parse_local_repository("/path/to/repo")

# Generate documentation
readme_content = llm_agent.generate_readme_content(
    ast_data=ast_data,
    files_content=files_content,
    style="summary"
)
```

## 📁 Project Structure

```
{{ project_structure }}
```

## 🔑 Configuration

Set the following environment variables:

- `OPENROUTER_API_KEY`: Your OpenRouter API key for LLM access
- `GITHUB_TOKEN`: Your GitHub token for repository access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenRouter for LLM API access
- GitHub for repository hosting and API
- All contributors who help improve this project

---

*Generated automatically by LLM AutoDoc* 