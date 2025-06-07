from setuptools import setup, find_packages

setup(
    name="llm-autodoc",
    version="0.1.2",
    description="Автоматическая генерация документации README с помощью LLM",
    author="Твоё Имя",
    author_email="your@email.com",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["app", "app.*"]),
    install_requires=[
        "click",
        "python-dotenv",
        "PyGithub",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "autodoc=app.cli:generate_readme",  # CLI-команда → функция в cli.py
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
