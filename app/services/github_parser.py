# app/services/github_parser.py

import logging
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from github import (
    Github,
    GithubException,
    RateLimitExceededException,
    UnknownObjectException,
)

# Configure logging for GitHub parsing
logging.basicConfig(level=logging.INFO)
github_logger = logging.getLogger("github_parser")

# Загрузка переменных окружения, если этот файл запускается отдельно (для тестирования)
# В основном приложении Streamlit это обычно делается в главном файле ui.py
if __name__ == "__main__":
    load_dotenv(
        dotenv_path="../../.env"
    )  # Укажите правильный путь к .env, если тестируете локально


class GithubParser:
    """
    Сервис для взаимодействия с GitHub API с целью получения файлов репозитория и их содержимого.
    """

    # Расширения файлов, которые мы считаем кодом или важными для документации
    # Можно будет настроить через параметр target_languages
    DEFAULT_CODE_EXTENSIONS = [
        ".py",
        ".go",
        ".ts",
        ".js",
        ".jsx",
        ".tsx",
        ".java",
        ".kt",
        ".swift",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".rs",
        ".scala",
        ".sh",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".xml",
        ".html",
        ".css",
        ".scss",
        ".less",  # Добавим немного фронтенда и конфигов
    ]
    MAX_FILE_SIZE_BYTES = (
        3 * 1024 * 1024
    )  # 1 MB, ограничение на размер файла для загрузки через API

    def __init__(self, github_token: Optional[str] = None):
        """
        Инициализирует GithubParser.

        Args:
            github_token: Токен GitHub API. Если не предоставлен, пытается загрузить GITHUB_TOKEN_AUTODOC из .env.
        """
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN_AUTODOC")

        if not github_token:
            raise ValueError(
                "Токен GitHub API не предоставлен. "
                "Передайте его в конструктор или установите переменную окружения GITHUB_TOKEN_AUTODOC."
            )
        try:
            self.github_client = Github(github_token)
            # Проверим токен, сделав простой запрос
            _ = self.github_client.get_user().login
            print("GithubParser успешно инициализирован и токен валиден.")
        except RateLimitExceededException:
            print(
                "Ошибка инициализации GithubParser: Превышен лимит запросов GitHub API."
            )
            raise
        except GithubException as e:
            if e.status == 401:  # Unauthorized
                print(
                    "Ошибка инициализации GithubParser: Невалидный токен GitHub API (401 Unauthorized)."
                )
            else:
                print(f"Ошибка инициализации GithubParser при проверке токена: {e}")
            raise

        self.files_processed_count = 0

    def _extract_repo_name_from_url(self, repo_url: str) -> Optional[str]:
        """
        Извлекает 'owner/repository' из URL GitHub.
        Поддерживаемые форматы:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - http://github.com/owner/repo
        - git@github.com:owner/repo.git
        """
        patterns = [
            r"https://github\.com/([^/]+/[^/.]+?)(\.git)?/?(?:/|$)",
            r"http://github\.com/([^/]+/[^/.]+?)(\.git)?/?(?:/|$)",
            r"git@github\.com:([^/]+/[^/.]+?)\.git$",
        ]
        for pattern in patterns:
            match = re.search(pattern, repo_url.strip())
            if match:
                return match.group(1)
        print(f"Предупреждение: Не удалось извлечь имя репозитория из URL: {repo_url}")
        return None

    def _extract_pr_info_from_url(self, pr_url: str) -> Optional[tuple[str, int]]:
        """
        Извлекает информацию о репозитории и номере PR из URL PR.
        Поддерживаемые форматы:
        - https://github.com/owner/repo/pull/123
        - https://github.com/owner/repo/pull/123/files
        - https://github.com/owner/repo/pull/123#issuecomment-123456

        Returns:
            Tuple (repo_name, pr_number) или None если не удалось распарсить
        """
        pattern = r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url.strip())
        if match:
            repo_name = match.group(1)
            pr_number = int(match.group(2))
            return repo_name, pr_number

        github_logger.warning(f"⚠️ Не удалось извлечь информацию о PR из URL: {pr_url}")
        return None

    def _fetch_files_recursively(
        self,
        repo: Any,  # Тип github.Repository.Repository
        path: str,
        branch: str,
        allowed_extensions: List[str],
    ) -> Dict[str, str]:
        """
        Рекурсивно получает файлы из указанного пути в репозитории.
        """
        files_data: Dict[str, str] = {}
        try:
            contents = repo.get_contents(path, ref=branch)
        except UnknownObjectException:
            print(
                f"Предупреждение: Путь или ветка не найдены: '{path}' на ветке '{branch}'"
            )
            return files_data
        except RateLimitExceededException:
            print(
                "Критическая ошибка: Превышен лимит запросов GitHub API во время рекурсивного обхода."
            )
            raise
        except GithubException as e:
            print(
                f"Ошибка GitHub API при получении содержимого для '{path}' на ветке '{branch}': {e.data.get('message', str(e))}"
            )
            return files_data

        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            self.files_processed_count += 1
            if self.files_processed_count % 20 == 0:  # Логируем каждые N файлов
                print(
                    f"Обработано {self.files_processed_count} элементов в репозитории..."
                )

            if item.type == "dir":
                # print(f"Вход в директорию: {item.path}")
                files_data.update(
                    self._fetch_files_recursively(
                        repo, item.path, branch, allowed_extensions
                    )
                )
            elif item.type == "file":
                _, ext = os.path.splitext(item.name)
                if ext.lower() in allowed_extensions:
                    # print(f"Найден подходящий файл: {item.path}")
                    if item.size > self.MAX_FILE_SIZE_BYTES:
                        print(
                            f"Пропуск большого файла (>{item.size / (1024*1024):.2f}MB): {item.path}"
                        )
                        continue

                    try:
                        # item.content доступен только если файл не слишком большой и не бинарный
                        # decoded_content уже обработан PyGithub
                        if (
                            hasattr(item, "decoded_content")
                            and item.decoded_content is not None
                        ):
                            file_content = item.decoded_content.decode(
                                "utf-8", errors="ignore"
                            )
                            files_data[item.path] = file_content
                        else:
                            # Это может случиться для бинарных файлов или если content не был загружен
                            print(
                                f"Предупреждение: Содержимое для файла {item.path} недоступно или пусто."
                            )
                    except RateLimitExceededException:
                        print(
                            "Критическая ошибка: Превышен лимит запросов GitHub API при получении содержимого файла."
                        )
                        raise
                    except GithubException as e:
                        print(
                            f"Ошибка GitHub API при получении содержимого файла {item.path}: {e}"
                        )
                    except Exception as e:
                        print(
                            f"Неожиданная ошибка при декодировании содержимого файла {item.path}: {e}"
                        )
            # Можно добавить обработку item.type == "submodule" или symlink, если нужно

        return files_data

    def get_repo_files_content(
        self,
        repo_url: str,
        branch: Optional[
            str
        ] = None,  # По умолчанию будет использована default_branch репозитория
        target_languages: Optional[List[str]] = None,  # ['python', 'go', 'typescript']
    ) -> Dict[str, str]:
        """
        Получает содержимое всех релевантных файлов из указанного URL репозитория GitHub.

        Args:
            repo_url: Полный URL репозитория GitHub.
            branch: Ветка для получения файлов. Если None, используется ветка по умолчанию.
            target_languages: Список языков для фильтрации файлов (например, ['python', 'go']).
                              Если None, используются DEFAULT_CODE_EXTENSIONS.

        Returns:
            Словарь, где ключи - это пути к файлам, а значения - их содержимое.
            Возвращает пустой словарь в случае ошибки или если файлы не найдены.
        """
        self.files_processed_count = 0  # Сброс счетчика для каждого нового вызова

        lang_to_ext_map = {
            "python": [".py"],
            "golang": [".go"],
            "go": [".go"],
            "typescript": [".ts", ".tsx"],
            "javascript": [".js", ".jsx"],
            "java": [".java"],
            "kotlin": [".kt"],
            "markdown": [".md", ".markdown"],
            # Добавьте другие языки и их расширения по мере необходимости
        }

        current_allowed_extensions: List[str]
        if target_languages:
            current_allowed_extensions = []
            for lang in target_languages:
                lang_lower = lang.lower()
                if lang_lower in lang_to_ext_map:
                    current_allowed_extensions.extend(lang_to_ext_map[lang_lower])
                else:
                    print(
                        f"Предупреждение: Неизвестный язык '{lang}' в target_languages. Используйте известные расширения или добавьте маппинг."
                    )
            if not current_allowed_extensions:  # Если языки не распознаны
                print(
                    "Предупреждение: Не удалось определить расширения для target_languages. Используются расширения по умолчанию."
                )
                current_allowed_extensions = self.DEFAULT_CODE_EXTENSIONS
        else:
            current_allowed_extensions = self.DEFAULT_CODE_EXTENSIONS

        # Приводим все расширения к нижнему регистру и обеспечиваем наличие точки
        current_allowed_extensions = list(
            set(
                [
                    ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                    for ext in current_allowed_extensions
                ]
            )
        )

        print(f"Целевые расширения файлов: {current_allowed_extensions}")

        # Log GitHub parsing start
        github_logger.info(f"🔍 Starting GitHub parsing for repository: {repo_url}")
        github_logger.info(f"📋 Target file extensions: {current_allowed_extensions}")
        if target_languages:
            github_logger.info(f"🎯 Target languages: {target_languages}")

        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            github_logger.error(
                f"❌ Failed to extract repository name from URL: {repo_url}"
            )
            print(
                f"Ошибка: Некорректный URL репозитория или не удалось извлечь owner/repo: {repo_url}"
            )
            return {}

        try:
            print(f"Доступ к репозиторию: {repo_full_name}")
            github_logger.info(f"🔗 Accessing repository: {repo_full_name}")
            repo = self.github_client.get_repo(repo_full_name)

            # Log repository info
            github_logger.info(
                f"📊 Repository info - Name: {repo.name}, Stars: {repo.stargazers_count}, Language: {repo.language}"
            )
            github_logger.info(
                f"📝 Repository description: {repo.description or 'No description'}"
            )

            if branch:
                try:
                    repo.get_branch(branch)  # Проверяем существование ветки
                    print(f"Используется указанная ветка: '{branch}'")
                except UnknownObjectException:
                    print(
                        f"Предупреждение: Указанная ветка '{branch}' не найдена в {repo_full_name}."
                    )
                    try:
                        default_branch = repo.default_branch
                        print(
                            f"Попытка использовать ветку по умолчанию: '{default_branch}'"
                        )
                        branch = default_branch
                    except Exception as e_def_branch:
                        print(
                            f"Критическая ошибка: Не удалось определить ветку по умолчанию для {repo_full_name}: {e_def_branch}"
                        )
                        return {}
            else:  # branch is None
                branch = repo.default_branch
                print(f"Используется ветка по умолчанию: '{branch}'")

            print(f"Получение файлов из {repo_full_name} (ветка: {branch})...")
            github_logger.info(f"🌿 Using branch: {branch}")
            github_logger.info(f"📁 Starting recursive file fetch from root directory")

            all_files_content = self._fetch_files_recursively(
                repo, "", branch, current_allowed_extensions
            )  # Начинаем с корневой директории

            print(f"Завершено. Найдено {len(all_files_content)} релевантных файлов.")

            # Log detailed file information
            github_logger.info(
                f"✅ GitHub parsing completed. Found {len(all_files_content)} relevant files"
            )

            total_size = 0
            for file_path, content in all_files_content.items():
                file_size = len(content.encode("utf-8"))
                total_size += file_size
                # Log first few lines of each file for debugging
                preview = content[:200].replace("\n", "\\n").replace("\r", "\\r")
                github_logger.info(
                    f"📄 File: {file_path} | Size: {file_size} bytes | Preview: {preview}..."
                )

            github_logger.info(
                f"📊 Total content size: {total_size} bytes ({total_size/1024:.1f} KB)"
            )

            return all_files_content

        except UnknownObjectException:
            print(f"Ошибка: Репозиторий '{repo_full_name}' не найден или недоступен.")
            return {}
        except RateLimitExceededException:
            print(
                "Критическая ошибка: Превышен лимит запросов GitHub API. Попробуйте позже или проверьте токен."
            )
            return {}  # В этом случае лучше остановить выполнение
        except GithubException as e:  # Более общая ошибка GitHub API
            print(
                f"Произошла ошибка GitHub API: {e.data.get('message', str(e))} (Status: {e.status})"
            )
            return {}
        except Exception as e:
            import traceback

            print(f"Произошла непредвиденная ошибка: {e}")
            traceback.print_exc()  # Для отладки
            return {}

    def check_readme_exists(self, repo_url: str, branch: Optional[str] = None) -> bool:
        """
        Check if README file exists in the repository.

        Args:
            repo_url: Full GitHub repository URL
            branch: Branch to check. If None, uses default branch

        Returns:
            True if README exists, False otherwise
        """
        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            print(f"Error: Invalid repository URL: {repo_url}")
            return False

        try:
            repo = self.github_client.get_repo(repo_full_name)

            if not branch:
                branch = repo.default_branch

            # Common README file names
            readme_names = [
                "README.md",
                "readme.md",
                "README.MD",
                "README",
                "readme",
                "Readme.md",
            ]

            for readme_name in readme_names:
                try:
                    repo.get_contents(readme_name, ref=branch)
                    github_logger.info(f"✅ Found README file: {readme_name}")
                    return True
                except UnknownObjectException:
                    continue

            github_logger.info("❌ No README file found in repository")
            return False

        except Exception as e:
            github_logger.error(f"❌ Error checking README existence: {e}")
            return False

    def get_recent_merged_prs(
        self, repo_url: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent merged pull requests from the repository.

        Args:
            repo_url: Full GitHub repository URL
            limit: Maximum number of PRs to retrieve

        Returns:
            List of dictionaries containing PR information
        """
        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            print(f"Error: Invalid repository URL: {repo_url}")
            return []

        try:
            repo = self.github_client.get_repo(repo_full_name)

            # Get merged PRs (state='closed' and merged=True)
            pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")

            merged_prs = []
            count = 0

            for pr in pulls:
                if count >= limit:
                    break

                if pr.merged:
                    pr_info = {
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body or "",
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "user": pr.user.login if pr.user else "Unknown",
                        "url": pr.html_url,
                        "files_changed": [],
                    }

                    # Get files changed in this PR
                    try:
                        files = pr.get_files()
                        for file in files:
                            pr_info["files_changed"].append(
                                {
                                    "filename": file.filename,
                                    "status": file.status,  # added, modified, removed
                                    "additions": file.additions,
                                    "deletions": file.deletions,
                                    "changes": file.changes,
                                }
                            )
                    except Exception as e:
                        github_logger.warning(
                            f"⚠️ Could not get files for PR #{pr.number}: {e}"
                        )

                    merged_prs.append(pr_info)
                    count += 1

            github_logger.info(f"📋 Retrieved {len(merged_prs)} recent merged PRs")
            return merged_prs

        except Exception as e:
            github_logger.error(f"❌ Error getting recent PRs: {e}")
            return []

    def get_existing_readme_content(
        self, repo_url: str, branch: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the content of existing README file from the repository.

        Args:
            repo_url: Full GitHub repository URL
            branch: Branch to check. If None, uses default branch

        Returns:
            README content as string, or None if not found
        """
        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            print(f"Error: Invalid repository URL: {repo_url}")
            return None

        try:
            repo = self.github_client.get_repo(repo_full_name)

            if not branch:
                branch = repo.default_branch

            # Common README file names
            readme_names = [
                "README.md",
                "readme.md",
                "README.MD",
                "README",
                "readme",
                "Readme.md",
            ]

            for readme_name in readme_names:
                try:
                    readme_file = repo.get_contents(readme_name, ref=branch)
                    if (
                        hasattr(readme_file, "decoded_content")
                        and readme_file.decoded_content
                    ):
                        content = readme_file.decoded_content.decode(
                            "utf-8", errors="ignore"
                        )
                        github_logger.info(
                            f"✅ Retrieved README content from: {readme_name}"
                        )
                        return content
                except UnknownObjectException:
                    continue

            github_logger.info("❌ No README file found in repository")
            return None

        except Exception as e:
            github_logger.error(f"❌ Error getting README content: {e}")
            return None

    def get_pr_details(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific pull request.

        Args:
            repo_url: Full GitHub repository URL
            pr_number: Pull request number

        Returns:
            Dictionary containing detailed PR information including file changes, or None if not found
        """
        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            print(f"Error: Invalid repository URL: {repo_url}")
            return None

        try:
            repo = self.github_client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            pr_info = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "merged": pr.merged,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "user": pr.user.login if pr.user else "Unknown",
                "url": pr.html_url,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files_changed": [],
                "commits": [],
            }

            # Get files changed in this PR with detailed diff information
            try:
                files = pr.get_files()
                for file in files:
                    file_info = {
                        "filename": file.filename,
                        "status": file.status,  # added, modified, removed, renamed
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "patch": file.patch if hasattr(file, "patch") else None,
                    }
                    pr_info["files_changed"].append(file_info)
            except Exception as e:
                github_logger.warning(f"⚠️ Could not get files for PR #{pr.number}: {e}")

            # Get commits in this PR
            try:
                commits = pr.get_commits()
                for commit in commits:
                    commit_info = {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": (
                            commit.commit.author.name
                            if commit.commit.author
                            else "Unknown"
                        ),
                        "date": (
                            commit.commit.author.date.isoformat()
                            if commit.commit.author and commit.commit.author.date
                            else None
                        ),
                    }
                    pr_info["commits"].append(commit_info)
            except Exception as e:
                github_logger.warning(
                    f"⚠️ Could not get commits for PR #{pr.number}: {e}"
                )

            github_logger.info(f"📋 Retrieved detailed information for PR #{pr.number}")
            return pr_info

        except UnknownObjectException:
            github_logger.error(
                f"❌ PR #{pr_number} not found in repository {repo_full_name}"
            )
            return None
        except Exception as e:
            github_logger.error(f"❌ Error getting PR #{pr_number} details: {e}")
            return None

    def get_pr_details_by_url(self, pr_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific pull request by its URL.

        Args:
            pr_url: Full GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Dictionary containing detailed PR information including file changes, or None if not found
        """
        pr_info = self._extract_pr_info_from_url(pr_url)
        if not pr_info:
            print(f"Error: Invalid PR URL: {pr_url}")
            return None

        repo_name, pr_number = pr_info

        try:
            repo = self.github_client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            pr_info_dict = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "merged": pr.merged,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "user": pr.user.login if pr.user else "Unknown",
                "url": pr.html_url,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files_changed": [],
                "commits": [],
                "repo_name": repo_name,
            }

            # Get files changed in this PR with detailed diff information
            try:
                files = pr.get_files()
                for file in files:
                    file_info = {
                        "filename": file.filename,
                        "status": file.status,  # added, modified, removed, renamed
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "patch": file.patch if hasattr(file, "patch") else None,
                    }
                    pr_info_dict["files_changed"].append(file_info)
            except Exception as e:
                github_logger.warning(f"⚠️ Could not get files for PR #{pr.number}: {e}")

            # Get commits in this PR
            try:
                commits = pr.get_commits()
                for commit in commits:
                    commit_info = {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": (
                            commit.commit.author.name
                            if commit.commit.author
                            else "Unknown"
                        ),
                        "date": (
                            commit.commit.author.date.isoformat()
                            if commit.commit.author and commit.commit.author.date
                            else None
                        ),
                    }
                    pr_info_dict["commits"].append(commit_info)
            except Exception as e:
                github_logger.warning(
                    f"⚠️ Could not get commits for PR #{pr.number}: {e}"
                )

            github_logger.info(
                f"📋 Retrieved detailed information for PR #{pr.number} from URL"
            )
            return pr_info_dict

        except UnknownObjectException:
            github_logger.error(
                f"❌ PR #{pr_number} not found in repository {repo_name}"
            )
            return None
        except Exception as e:
            github_logger.error(f"❌ Error getting PR details from URL: {e}")
            return None
