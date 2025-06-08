# app/ui.py
import os
import sys

# Добавляем корневую директорию проекта (на один уровень выше 'app') в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import io
import logging
import zipfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.services.architecture_analyzer import ArchitectureAnalyzer
from app.services.ast_analyzer import AstAnalyzer
from app.services.doc_generator import (
    DocGenerator,  # Не используется в текущей логике README, но оставлен
)
from app.services.github_parser import GithubParser
from app.services.llm_agent import LlmAgent  # Уже импортирован, все ок

load_dotenv()  # Загружаем .env из корня проекта

# Configure logging for main UI
logging.basicConfig(level=logging.INFO)
ui_logger = logging.getLogger("ui_main")

# --- Новые корпоративные цвета Lamoda Tech ---
LAMODA_LIME_ACCENT = "#CDFE00"
LAMODA_BLACK_BG = "#000000"
LAMODA_WHITE_TEXT = "#FFFFFF"
LAMODA_BLACK_TEXT_ON_LIME = "#000000"
LAMODA_DARK_GRAY_SUBTLE = "#1A1A1A"
LAMODA_MID_GRAY_BORDER = "#333333"
LAMODA_LIGHT_GRAY_TEXT = "#B8B8B8"

st.set_page_config(
    page_title="AI AutoDoc Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
    /* ... (ваши стили остаются без изменений) ... */
    body {{
        color: {LAMODA_WHITE_TEXT};
    }}
    .main .block-container {{
        background-color: {LAMODA_BLACK_BG};
        padding-top: 2rem;
        padding-bottom: 2rem;
        color: {LAMODA_WHITE_TEXT};
    }}
    .stButton button {{
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
    }}
    .stButton button[data-testid="baseButton-secondary"],
    .stDownloadButton button {{
        background-color: {LAMODA_LIME_ACCENT};
        color: {LAMODA_BLACK_TEXT_ON_LIME};
    }}
    .stButton button[data-testid="baseButton-secondary"]:hover,
    .stDownloadButton button:hover {{
        background-color: #B8E400;
        color: {LAMODA_BLACK_TEXT_ON_LIME};
    }}
    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea {{
        background-color: {LAMODA_DARK_GRAY_SUBTLE};
        color: {LAMODA_WHITE_TEXT};
        border: 1px solid {LAMODA_MID_GRAY_BORDER};
        border-radius: 8px;
    }}
    .stTextInput input:focus,
    .stTextArea textarea:focus {{
        border-color: {LAMODA_LIME_ACCENT};
        box-shadow: 0 0 0 0.1rem {LAMODA_LIME_ACCENT}40;
    }}
    .stTextInput ::placeholder,
    .stTextArea ::placeholder {{
        color: #888888;
    }}
    .sidebar .sidebar-content {{
        background-color: {LAMODA_BLACK_BG};
        padding: 2rem 1.5rem;
    }}
    div[data-testid="stSidebarNavItems"] {{
        padding-top: 1rem;
    }}
    .sidebar .sidebar-content h1,
    .sidebar .sidebar-content h2,
    .sidebar .sidebar-content h3,
    .sidebar .sidebar-content p,
    .sidebar .sidebar-content label {{
        color: {LAMODA_WHITE_TEXT} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {LAMODA_WHITE_TEXT};
        font-weight: 600;
    }}
    .lamoda-lime-text {{
        color: {LAMODA_LIME_ACCENT};
    }}
    .readme-container {{
        background-color: {LAMODA_DARK_GRAY_SUBTLE};
        color: {LAMODA_WHITE_TEXT};
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid {LAMODA_MID_GRAY_BORDER};
        margin-top: 1.5rem;
        max-height: 70vh;
        overflow-y: auto;
    }}
    .readme-container h1, .readme-container h2, .readme-container h3 {{
        margin-top: 1em;
        margin-bottom: 0.5em;
        color: {LAMODA_LIME_ACCENT};
    }}
    .readme-container p {{
        line-height: 1.6;
        color: {LAMODA_WHITE_TEXT};
    }}
    .readme-container code {{
        background-color: {LAMODA_MID_GRAY_BORDER};
        color: {LAMODA_LIME_ACCENT};
        padding: 0.2em 0.4em;
        border-radius: 4px;
        font-size: 0.9em;
    }}
    .readme-container pre {{
        background-color: {LAMODA_BLACK_BG};
        border: 1px solid {LAMODA_MID_GRAY_BORDER};
        padding: 1em;
        border-radius: 6px;
        overflow-x: auto;
    }}
    .readme-container pre code {{
        background-color: transparent !important;
        color: {LAMODA_WHITE_TEXT};
        padding: 0;
    }}
    .logo-text-la {{
        color: {LAMODA_WHITE_TEXT};
    }}
    .logo-text-tech {{
        color: {LAMODA_LIME_ACCENT};
        font-weight: 700;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# --- Инициализация сервисов ---
@st.cache_resource
def get_services():
    github_token = os.getenv("GITHUB_TOKEN_AUTODOC")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not github_token:
        st.sidebar.error(
            "GITHUB_TOKEN_AUTODOC не найден в .env. Пожалуйста, добавьте его."
        )
        st.stop()
    if not openrouter_api_key:
        st.sidebar.warning(
            "OPENROUTER_API_KEY не найден в .env. Генерация документации через LLM будет недоступна или вернет ошибку."
        )
    return {
        "github_parser": GithubParser(github_token=github_token),
        "ast_analyzer": AstAnalyzer(),
        "architecture_analyzer": ArchitectureAnalyzer(),
        "llm_agent": LlmAgent(openrouter_api_key=openrouter_api_key),
        "doc_generator": DocGenerator(template_dir="app/templates"),
    }


services = get_services()
github_parser = services["github_parser"]
ast_analyzer = services["ast_analyzer"]
architecture_analyzer = services["architecture_analyzer"]
llm_agent = services["llm_agent"]


# --- Функция для создания ZIP архива с документацией ---
def create_docs_zip(docs_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in docs_dict.items():
            zip_file.writestr(file_path, content)
    return zip_buffer.getvalue()


# --- Функция для группировки файлов по папкам ---
def group_files_by_folder(files_content):
    folders = {}
    for file_path, content in files_content.items():
        path_parts = Path(file_path).parts
        if len(path_parts) > 1:
            folder = path_parts[0]
        else:
            folder = "root"

        if folder not in folders:
            folders[folder] = {}
        folders[folder][file_path] = content

    return folders


# --- Состояние приложения ---
if "generated_readme" not in st.session_state:
    st.session_state.generated_readme = None
if "last_action" not in st.session_state:
    st.session_state.last_action = None
if "last_pr_number" not in st.session_state:
    st.session_state.last_pr_number = None
if "generated_docs" not in st.session_state:
    st.session_state.generated_docs = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None

# --- UI ---
# Шапка
st.markdown(
    f"""
<div style="display: flex; align-items: center; margin-bottom: 2rem; padding: 1rem; background-color: {LAMODA_BLACK_BG}; border-bottom: 1px solid {LAMODA_MID_GRAY_BORDER};">
    <div style="font-size: 3rem; margin-right: 20px; color: {LAMODA_LIME_ACCENT};">📄</div>
    <div>
        <h1 style="margin: 0; padding: 0; font-weight: 600;">
            <span class="logo-text-la">AI Auto</span><span class="logo-text-tech">Doc</span>
        </h1>
        <div style="color: #AAAAAA; font-size: 1.1rem; margin-top: 5px;">
            Автоматическая генерация документации для вашего проекта
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Сайдбар для ввода данных
with st.sidebar:
    st.markdown(
        f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 2.5rem; color: {LAMODA_LIME_ACCENT}; margin-bottom: 10px;">⚙️</div>
        <h2 style="font-weight: 600; font-size: 1.4rem;">Настройки проекта</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    repo_url = st.text_input(
        "🔗 URL GitHub репозитория",
        placeholder="https://github.com/owner/repository",
        help="Введите полный URL публичного GitHub репозитория (для генерации документации).",
    )

    # выбор модели LLM
    available_models = list(LlmAgent.DEFAULT_MODEL_MAPPING.keys())
    selected_model_key = st.selectbox(
        "🤖 Выберите модель LLM",
        options=available_models,
        index=available_models.index(llm_agent.default_model_key),
    )

    # выбор режима генерации
    doc_mode = st.selectbox(
        "📚 Режим генерации документации",
        options=["single_readme", "docs_folder"],
        format_func=lambda x: (
            "📄 Один README.md"
            if x == "single_readme"
            else "📁 Папка docs (MD для каждой папки)"
        ),
        index=0,
    )

    # Поле для ввода URL PR
    pr_url = st.text_input(
        "🔗 URL Pull Request для Release Notes",
        placeholder="https://github.com/owner/repo/pull/123",
        help="Введите полную ссылку на Pull Request для генерации release notes",
    )

    # Создаем две колонки для кнопок
    col1, col2 = st.columns(2)
    with col1:
        generate_clicked = st.button(
            "✨ Сгенерировать", type="secondary", use_container_width=True
        )
    with col2:
        release_notes_clicked = st.button(
            "📝 Release Notes", type="secondary", use_container_width=True
        )

    if generate_clicked:
        if repo_url:
            st.session_state.generated_readme = None
            st.session_state.generated_docs = None
            st.session_state.error_message = None
            st.session_state.last_action = "generate"
            st.session_state.last_pr_number = None

            ui_logger.info(
                f"🚀 Starting documentation generation process for repository: {repo_url}"
            )

            try:
                with st.spinner("🚀 Магия ИИ в действии... Пожалуйста, подождите..."):
                    spinner_placeholder = st.empty()
                    spinner_placeholder.text("1/4: Получение файлов из репозитория...")
                    ui_logger.info("📁 Step 1/4: Fetching files from repository")

                    files_content = github_parser.get_repo_files_content(repo_url)
                    if not files_content:
                        ui_logger.error("❌ Failed to fetch files from repository")
                        st.session_state.error_message = (
                            "Не удалось получить файлы или репозиторий пуст/недоступен."
                        )
                        spinner_placeholder.empty()
                        st.rerun()

                    ui_logger.info(
                        f"✅ Step 1/4 completed: Retrieved {len(files_content)} files"
                    )

                    spinner_placeholder.text("2/4: Анализ структуры кода (AST)...")
                    ast_data = ast_analyzer.analyze_repository(files_content)

                    if doc_mode == "single_readme":
                        spinner_placeholder.text(
                            "3/4: Генерация README с помощью LLM..."
                        )
                        llm_output = llm_agent.generate_readme_content(
                            ast_data,
                            files_content,
                            model_key=selected_model_key,
                            style="summary",
                        )

                        if llm_output.startswith("⚠️ Ошибка") or llm_output.startswith(
                            "# Ошибка"
                        ):
                            st.session_state.error_message = (
                                f"Ошибка от LLM: {llm_output}"
                            )
                            spinner_placeholder.empty()
                            st.rerun()

                        spinner_placeholder.text(
                            "4/4: Формирование финального README.md..."
                        )
                        st.session_state.generated_readme = llm_output

                    else:  # docs_folder
                        spinner_placeholder.text("3/4: Группировка файлов по папкам...")
                        folders = group_files_by_folder(files_content)

                        spinner_placeholder.text(
                            "4/4: Генерация документации для каждой папки..."
                        )
                        docs_dict = {}

                        for folder_name, folder_files in folders.items():
                            folder_ast_data = ast_analyzer.analyze_repository(
                                folder_files
                            )

                            doc_content = llm_agent.generate_folder_documentation(
                                folder_name=folder_name,
                                ast_data=folder_ast_data,
                                files_content=folder_files,
                                model_key=selected_model_key,
                            )

                            if not doc_content.startswith(
                                "⚠️ Ошибка"
                            ) and not doc_content.startswith("# Ошибка"):
                                docs_dict[f"docs/{folder_name}.md"] = doc_content

                        if docs_dict:
                            # Создаем основной README для папки docs
                            main_readme = llm_agent.generate_main_docs_readme(
                                folders=list(folders.keys()),
                                ast_data=ast_data,
                                model_key=selected_model_key,
                            )
                            docs_dict["docs/README.md"] = main_readme
                            st.session_state.generated_docs = docs_dict
                        else:
                            st.session_state.error_message = (
                                "Не удалось сгенерировать документацию для папок."
                            )
                            spinner_placeholder.empty()
                            st.rerun()

                    spinner_placeholder.empty()
                    st.success("🎉 Документация успешно сгенерирована!")

            except Exception as e:
                st.session_state.error_message = (
                    f"Произошла непредвиденная ошибка: {str(e)}"
                )
                print(f"UI Error: {e}")
                import traceback

                traceback.print_exc()
                if "spinner_placeholder" in locals():
                    spinner_placeholder.empty()
                st.rerun()
        else:
            st.sidebar.warning("Пожалуйста, введите URL репозитория.")

    if release_notes_clicked:
        if pr_url:
            st.session_state.generated_readme = None
            st.session_state.generated_docs = None
            st.session_state.error_message = None
            st.session_state.last_action = "release_notes"

            ui_logger.info(f"📝 Starting release notes generation for PR URL: {pr_url}")

            try:
                with st.spinner(
                    f"📝 Генерация Release Notes для PR... Пожалуйста, подождите..."
                ):
                    spinner_placeholder = st.empty()

                    spinner_placeholder.text(f"1/2: Получение информации о PR...")
                    ui_logger.info(f"📋 Step 1/2: Fetching PR details from URL")

                    pr_info = github_parser.get_pr_details_by_url(pr_url)
                    if not pr_info:
                        st.session_state.error_message = (
                            f"❌ Не удалось найти PR по указанной ссылке. "
                            "Проверьте URL и убедитесь, что PR существует."
                        )
                        spinner_placeholder.empty()
                        st.rerun()

                    # Сохраняем номер PR для отображения
                    st.session_state.last_pr_number = pr_info.get("number")

                    spinner_placeholder.text(
                        f"2/2: Генерация Release Notes с помощью LLM..."
                    )
                    ui_logger.info(f"🤖 Step 2/2: Generating release notes with LLM")

                    release_notes = llm_agent.generate_release_notes(
                        pr_info=pr_info,
                        model_key=selected_model_key,
                    )

                    if release_notes.startswith("⚠️ Ошибка") or release_notes.startswith(
                        "# Ошибка"
                    ):
                        st.session_state.error_message = (
                            f"Ошибка от LLM: {release_notes}"
                        )
                        spinner_placeholder.empty()
                        st.rerun()

                    st.session_state.generated_readme = release_notes
                    spinner_placeholder.empty()
                    st.success(
                        f"🎉 Release Notes для PR #{pr_info.get('number')} успешно сгенерированы!"
                    )

            except Exception as e:
                st.session_state.error_message = f"Произошла непредвиденная ошибка при генерации release notes: {str(e)}"
                print(f"UI Release Notes Error: {e}")
                import traceback

                traceback.print_exc()
                if "spinner_placeholder" in locals():
                    spinner_placeholder.empty()
                st.rerun()
        else:
            st.sidebar.warning("Пожалуйста, введите URL Pull Request.")

# Основная область для вывода
if st.session_state.error_message:
    st.error(f"🚫 {st.session_state.error_message}")

if st.session_state.generated_readme:
    st.markdown("---")
    # Определяем заголовок и имя файла в зависимости от того, что было сгенерировано
    if (
        st.session_state.last_action == "release_notes"
        and st.session_state.last_pr_number
    ):
        st.subheader(f"📝 Release Notes для PR #{st.session_state.last_pr_number}")
        download_label = "💾 Скачать Release Notes"
        file_name = f"release_notes_PR_{st.session_state.last_pr_number}.md"
    else:
        st.subheader("📄 Сгенерированный README.md")
        download_label = "💾 Скачать README.md"
        file_name = "README_generated.md"

    st.markdown(
        f"""
    <div class="readme-container">
    {st.session_state.generated_readme}
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.download_button(
        label=download_label,
        data=st.session_state.generated_readme,
        file_name=file_name,
        mime="text/markdown",
        use_container_width=True,
        type="secondary",
    )

if st.session_state.generated_docs:
    st.markdown("---")
    st.subheader("📁 Сгенерированная документация папок")

    # Показываем превью каждого файла
    for file_path, content in st.session_state.generated_docs.items():
        with st.expander(f"📄 {file_path}"):
            st.markdown(
                f"""
            <div class="readme-container">
            {content}
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Кнопка скачивания ZIP архива
    zip_data = create_docs_zip(st.session_state.generated_docs)
    st.download_button(
        label="📦 Скачать папку docs (ZIP)",
        data=zip_data,
        file_name="docs_generated.zip",
        mime="application/zip",
        use_container_width=True,
        type="secondary",
    )


elif not st.session_state.error_message and not st.session_state.generated_docs:
    st.info(
        "👋 Добро пожаловать! Введите URL GitHub репозитория в панели слева и выберите нужное действие."
    )
    st.markdown(
        f"""
    #### 🚀 Доступные режимы:
    **📄 Один README.md** - создание единого README файла:
    1. Загрузка файлов из репозитория
    2. Анализ структуры кода (AST)
    3. Генерация общего описания проекта
    4. Готовый README.md для скачивания

    **📁 Папка docs** - создание детальной документации:
    1. Группировка файлов по папкам проекта
    2. Анализ каждой папки отдельно
    3. Генерация MD файла для каждой папки
    4. Создание основного README.md для папки docs
    5. Скачивание ZIP архива с полной документацией

    **📝 Release Notes** - генерация changelog на основе конкретного Pull Request:
    1. Введите полную ссылку на PR (например, https://github.com/owner/repo/pull/123)
    2. Анализ изменений в файлах и коммитах
    3. Генерация структурированных release notes
    4. Готовый changelog в формате Markdown
    """
    )

st.markdown("---")
st.markdown(
    f"""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, {LAMODA_DARK_GRAY_SUBTLE} 0%, rgba(26,26,26,0.5) 100%); border-radius: 12px; margin-top: 2rem;">
    <div style="font-size: 1rem; color: {LAMODA_LIGHT_GRAY_TEXT}; margin-bottom: 0.5rem;">
        Разработано командой MISISxHSExITMO на хакатоне Orion Soft
    </div>
    <div style="font-size: 1.2rem; font-weight: 600;">
        <span class="logo-text-la">lamoda</span><span class="logo-text-tech">tech</span> <span style="color: {LAMODA_LIGHT_GRAY_TEXT};"></span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
