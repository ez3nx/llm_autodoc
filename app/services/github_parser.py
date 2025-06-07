# app/services/github_parser.py

import os
import re
from typing import List, Dict, Optional, Any
from github import (
    Github,
    UnknownObjectException,
    RateLimitExceededException,
    GithubException,
)
from dotenv import load_dotenv

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
        1 * 1024 * 1024
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
            # Проверим токен, сделав простой запрос (например, к текущему пользователю)
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
            # print(f"DEBUG: Запрос содержимого для пути: '{path}', ветка: '{branch}'")
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
            return files_data  # Продолжаем, если это не критическая ошибка

        # get_contents может вернуть один элемент, если path - это файл
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

        repo_full_name = self._extract_repo_name_from_url(repo_url)
        if not repo_full_name:
            print(
                f"Ошибка: Некорректный URL репозитория или не удалось извлечь owner/repo: {repo_url}"
            )
            return {}

        try:
            print(f"Доступ к репозиторию: {repo_full_name}")
            repo = self.github_client.get_repo(repo_full_name)

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
            all_files_content = self._fetch_files_recursively(
                repo, "", branch, current_allowed_extensions
            )  # Начинаем с корневой директории

            print(f"Завершено. Найдено {len(all_files_content)} релевантных файлов.")
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


if __name__ == "__main__":
    # Пример использования для локального тестирования
    # Убедитесь, что у вас есть .env файл с GITHUB_TOKEN_AUTODOC в корне проекта или на два уровня выше
    print("Тестирование GithubParser...")
    try:
        parser = GithubParser()  # Токен должен загрузиться из .env

        # Пример репозитория для теста (замените на свой, если нужно)
        # test_repo_url = "https://github.com/streamlit/streamlit" # Большой репозиторий, может быть долго
        test_repo_url = "https://github.com/Korune/summarize.git"  # Небольшой репозиторий для быстрого теста
        # test_repo_url = "https://github.com/pallets/flask"

        print(f"\nТест 1: Получение Python файлов из {test_repo_url}")
        python_files = parser.get_repo_files_content(
            test_repo_url, target_languages=["python"]
        )
        if python_files:
            print(f"Найдено {len(python_files)} Python файлов. Первые несколько:")
            for i, (path, content_preview) in enumerate(list(python_files.items())[:3]):
                print(
                    f"  Файл: {path}, Размер: {len(content_preview)} байт, Превью: {content_preview[:100].replace(os.linesep, ' ')}..."
                )
        else:
            print("Python файлы не найдены или произошла ошибка.")

        print(f"\nТест 2: Получение всех файлов по умолчанию из {test_repo_url}")
        all_default_files = parser.get_repo_files_content(test_repo_url)
        if all_default_files:
            print(
                f"Найдено {len(all_default_files)} файлов (расширения по умолчанию). Первые несколько:"
            )
            for i, (path, content_preview) in enumerate(
                list(all_default_files.items())[:3]
            ):
                print(
                    f"  Файл: {path}, Размер: {len(content_preview)} байт, Превью: {content_preview[:100].replace(os.linesep, ' ')}..."
                )
        else:
            print("Файлы (расширения по умолчанию) не найдены или произошла ошибка.")

        # Тест с несуществующим репозиторием
        print("\nТест 3: Несуществующий репозиторий")
        non_existent_files = parser.get_repo_files_content(
            "https://github.com/nonexistentuser/nonexistentrepo"
        )
        if not non_existent_files:
            print(
                "ОК: Несуществующий репозиторий обработан корректно (файлы не найдены)."
            )

        # Тест с неправильным URL
        print("\nТест 4: Неправильный URL")
        invalid_url_files = parser.get_repo_files_content("htp:/githubcom/user/repo")
        if not invalid_url_files:
            print("ОК: Неправильный URL обработан корректно (файлы не найдены).")

    except ValueError as ve:
        print(f"Ошибка при инициализации или использовании парсера: {ve}")
    except Exception as e:
        print(f"Непредвиденная ошибка во время тестов: {e}")
