# app/ui.py
import os
import sys

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.express as px
from matplotlib.style.core import available

# Добавляем корневую директорию проекта (на один уровень выше 'app') в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging

import streamlit as st
from dotenv import load_dotenv

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
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")  # Получаем ключ для OpenRouter

    if not github_token:
        st.sidebar.error(
            "GITHUB_TOKEN_AUTODOC не найден в .env. Пожалуйста, добавьте его."
        )
        st.stop()

    # Ключ для LLM не является критичным для запуска самого UI,
    # но LLM функционал не будет работать без него.
    # LlmAgent сам выведет предупреждение в консоль, если ключ отсутствует.
    # Можно добавить st.sidebar.warning, если ключ не найден, но это опционально.
    if not openrouter_api_key:
        st.sidebar.warning(
            "OPENROUTER_API_KEY не найден в .env. Генерация документации через LLM будет недоступна или вернет ошибку."
        )

    return {
        "github_parser": GithubParser(github_token=github_token),
        "ast_analyzer": AstAnalyzer(),
        "llm_agent": LlmAgent(
            openrouter_api_key=openrouter_api_key
        ),  # Используем правильный ключ
        "doc_generator": DocGenerator(
            template_dir="app/templates"
        ),  # Оставлен, хотя не используется для README
    }


services = get_services()
github_parser = services["github_parser"]
ast_analyzer = services["ast_analyzer"]
llm_agent = services["llm_agent"]
# doc_generator = services["doc_generator"] # Раскомментируйте, если будете использовать

# --- Состояние приложения ---
if "generated_readme" not in st.session_state:
    st.session_state.generated_readme = None
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
        help="Введите полный URL публичного GitHub репозитория.",
    )

    # выбор модели LLM
    available_models = list(LlmAgent.DEFAULT_MODEL_MAPPING.keys())
    selected_model_key = st.selectbox(
        "🤖 Выберите модель LLM",
        options=available_models,
        index=available_models.index(
            llm_agent.default_model_key
        ),  # Устанавливаем дефолтное значение из агента
    )

    # выбор стиля README
    readme_style = st.selectbox(
        "🎨 Стиль README",
        options=["summary", "detailed"],
        index=0,  # "summary" по умолчанию
    )

    # Создаем две колонки для кнопок
    col1, col2 = st.columns(2)

    with col1:
        generate_clicked = st.button(
            "✨ Сгенерировать README", type="secondary", use_container_width=True
        )

    with col2:
        update_clicked = st.button(
            "🔄 Обновить README", type="secondary", use_container_width=True
        )

    if generate_clicked:
        if repo_url:
            st.session_state.generated_readme = None
            st.session_state.error_message = None

            # Log the start of README generation process
            ui_logger.info(
                f"🚀 Starting README generation process for repository: {repo_url}"
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

                    spinner_placeholder.text("3/4: Генерация описаний с помощью LLM...")
                    # Передаем выбранную модель и стиль, если добавили выбор в UI, иначе используются дефолтные
                    llm_output = llm_agent.generate_readme_content(
                        ast_data,
                        files_content,
                        model_key=selected_model_key,
                        style=readme_style,  # выбор стиля
                    )

                    if llm_output.startswith("⚠️ Ошибка") or llm_output.startswith(
                        "# Ошибка"
                    ):
                        st.session_state.error_message = f"Ошибка от LLM: {llm_output}"
                        spinner_placeholder.empty()
                        st.rerun()  # Перезапуск для отображения ошибки

                    spinner_placeholder.text(
                        "4/4: Формирование финального README.md..."
                    )
                    final_readme = llm_output
                    st.session_state.generated_readme = final_readme

                    spinner_placeholder.empty()
                    st.success("🎉 Документация успешно сгенерирована!")

            except Exception as e:
                st.session_state.error_message = (
                    f"Произошла непредвиденная ошибка: {str(e)}"
                )
                # st.exception(e) # Для детального трейсбека в UI, если нужно
                print(f"UI Error: {e}")  # Логируем ошибку в консоль
                import traceback

                traceback.print_exc()  # Печатаем полный трейсбек в консоль сервера
                if (
                    "spinner_placeholder" in locals()
                ):  # Проверяем, существует ли переменная
                    spinner_placeholder.empty()
                st.rerun()  # Перезапуск для отображения ошибки
        else:
            st.sidebar.warning("Пожалуйста, введите URL репозитория.")

    if update_clicked:
        if repo_url:
            st.session_state.generated_readme = None
            st.session_state.error_message = None

            # Log the start of README update process
            ui_logger.info(
                f"🔄 Starting README update process for repository: {repo_url}"
            )

            try:
                with st.spinner("🔄 Обновление README... Пожалуйста, подождите..."):
                    spinner_placeholder = st.empty()

                    # Step 1: Check if README exists
                    spinner_placeholder.text(
                        "1/5: Проверка наличия README в репозитории..."
                    )
                    ui_logger.info("📋 Step 1/5: Checking if README exists")

                    readme_exists = github_parser.check_readme_exists(repo_url)
                    if not readme_exists:
                        st.session_state.error_message = (
                            "❌ В вашем репозитории нет README файла. "
                            "Попробуйте сначала сгенерировать его с помощью кнопки 'Сгенерировать README'."
                        )
                        spinner_placeholder.empty()
                        st.rerun()

                    ui_logger.info("✅ Step 1/5 completed: README exists")

                    # Step 2: Get existing README content
                    spinner_placeholder.text("2/5: Получение существующего README...")
                    ui_logger.info("📄 Step 2/5: Getting existing README content")

                    existing_readme = github_parser.get_existing_readme_content(
                        repo_url
                    )
                    if not existing_readme:
                        st.session_state.error_message = "❌ Не удалось получить содержимое существующего README файла."
                        spinner_placeholder.empty()
                        st.rerun()

                    ui_logger.info("✅ Step 2/5 completed: Retrieved existing README")

                    # Step 3: Get recent merged PRs
                    spinner_placeholder.text("3/5: Получение последних merged PR...")
                    ui_logger.info("🔍 Step 3/5: Getting recent merged PRs")

                    recent_prs = github_parser.get_recent_merged_prs(repo_url, limit=10)
                    ui_logger.info(
                        f"✅ Step 3/5 completed: Found {len(recent_prs)} recent PRs"
                    )

                    # Check if there are any recent PRs
                    if not recent_prs:
                        st.session_state.error_message = None
                        spinner_placeholder.empty()
                        st.info(
                            "ℹ️ В репозитории нет недавних merged Pull Request'ов. "
                            "README не требует обновления, так как нет новых изменений для анализа."
                        )
                        ui_logger.info("ℹ️ No recent PRs found, skipping README update")
                    else:
                        # Show info about found PRs
                        spinner_placeholder.text(
                            f"Найдено {len(recent_prs)} недавних PR для анализа..."
                        )
                        ui_logger.info(
                            f"📋 Found {len(recent_prs)} recent PRs to analyze"
                        )

                        # Step 4: Get current repository state
                        spinner_placeholder.text(
                            "4/5: Анализ текущего состояния репозитория..."
                        )
                        ui_logger.info(
                            "📁 Step 4/5: Analyzing current repository state"
                        )

                        files_content = github_parser.get_repo_files_content(repo_url)
                        if not files_content:
                            st.session_state.error_message = (
                                "❌ Не удалось получить файлы репозитория для анализа."
                            )
                            spinner_placeholder.empty()
                            st.rerun()

                        ast_data = ast_analyzer.analyze_repository(files_content)
                        ui_logger.info(
                            "✅ Step 4/5 completed: Repository analysis done"
                        )

                        # Step 5: Update README with LLM
                        spinner_placeholder.text(
                            "5/5: Обновление README с помощью LLM..."
                        )
                        ui_logger.info("🤖 Step 5/5: Updating README with LLM")

                        updated_readme = llm_agent.update_readme_content(
                            existing_readme=existing_readme,
                            recent_prs=recent_prs,
                            ast_data=ast_data,
                            files_content=files_content,
                            model_key=selected_model_key,
                            style=readme_style,
                        )

                        if updated_readme.startswith(
                            "⚠️ Ошибка"
                        ) or updated_readme.startswith("# Ошибка"):
                            st.session_state.error_message = (
                                f"Ошибка от LLM: {updated_readme}"
                            )
                            spinner_placeholder.empty()
                            st.rerun()

                        st.session_state.generated_readme = updated_readme
                        spinner_placeholder.empty()

                        # Check if README was actually updated
                        if updated_readme.strip() == existing_readme.strip():
                            st.info(
                                "ℹ️ README не требует обновления. Последние изменения не влияют на документацию."
                            )
                        else:
                            st.success(
                                "🎉 README успешно обновлен на основе последних изменений!"
                            )

            except Exception as e:
                st.session_state.error_message = (
                    f"Произошла непредвиденная ошибка при обновлении README: {str(e)}"
                )
                print(f"UI Update Error: {e}")
                import traceback

                traceback.print_exc()
                if "spinner_placeholder" in locals():
                    spinner_placeholder.empty()
                st.rerun()
        else:
            st.sidebar.warning("Пожалуйста, введите URL репозитория.")

# Основная область для вывода
if st.session_state.error_message:
    st.error(
        f"🚫 {st.session_state.error_message}"
    )  # Убрал "Ошибка:" т.к. оно может быть в самой error_message

if st.session_state.generated_readme:
    st.markdown("---")
    st.subheader("📄 Сгенерированный README.md")
    st.markdown(
        f"""
    <div class="readme-container">
    {st.session_state.generated_readme}
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label="💾 Скачать README.md",
        data=st.session_state.generated_readme,
        file_name="README_generated.md",
        mime="text/markdown",
        use_container_width=True,
        type="secondary",  # Это сделает кнопку акцентной по вашим стилям
    )

    # 📊 Дополнительная аналитика по проекту
    st.markdown("---")
    st.markdown("## 📊 Аналитика и визуализация проекта", unsafe_allow_html=True)

    # 1. Распределение типов файлов
    st.markdown(
        f"""
    <div style="background-color:{LAMODA_DARK_GRAY_SUBTLE}; padding: 1.5rem; border-radius: 12px; border: 1px solid {LAMODA_MID_GRAY_BORDER}; margin-bottom: 2rem;">
    <h4 style="color: {LAMODA_LIME_ACCENT}; margin-bottom: 1rem;">📁 Распределение типов файлов в репозитории</h4>
    """,
        unsafe_allow_html=True,
    )

    # --- 1. Типы файлов
    file_extensions = [
        file.split(".")[-1] for file in files_content.keys() if "." in file
    ]
    ext_counts = pd.Series(file_extensions).value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(
        ext_counts.values, labels=ext_counts.index, autopct="%1.1f%%", startangle=140
    )
    ax1.axis("equal")
    st.pyplot(fig1)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. Структура проекта (treemap)
    st.markdown(
        f"""
    <div style="background-color:{LAMODA_DARK_GRAY_SUBTLE}; padding: 1.5rem; border-radius: 12px; border: 1px solid {LAMODA_MID_GRAY_BORDER}; margin-bottom: 2rem;">
    <h4 style="color: {LAMODA_LIME_ACCENT}; margin-bottom: 1rem;">🧱 Структура проекта (по размерам файлов)</h4>
    """,
        unsafe_allow_html=True,
    )

    tree_df = pd.DataFrame(
        [{"path": f, "size": len(content)} for f, content in files_content.items()]
    )
    fig2 = px.treemap(
        tree_df, path=["path"], values="size", title="Treemap", height=400
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. Пример диаграммы архитектуры (простая C4)
    st.markdown(
        f"""
    <div style="background-color:{LAMODA_DARK_GRAY_SUBTLE}; padding: 1.5rem; border-radius: 12px; border: 1px solid {LAMODA_MID_GRAY_BORDER};">
    <h4 style="color: {LAMODA_LIME_ACCENT}; margin-bottom: 1rem;">🧠 Архитектура (C4-пример)</h4>
    <p style="color: #AAAAAA;">Диаграмма компонентов приложения</p>
    """,
        unsafe_allow_html=True,
    )

    G = nx.DiGraph()
    G.add_edges_from(
        [
            ("👤 User", "🌐 API"),
            ("🌐 API", "🔧 Service"),
            ("🔧 Service", "💾 Repository"),
            ("💾 Repository", "🗄️ Database"),
        ]
    )
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    nx.draw(
        G,
        with_labels=True,
        node_color="#CDFE00",
        edge_color="gray",
        node_size=3000,
        font_size=10,
        font_weight="bold",
        ax=ax3,
    )
    st.pyplot(fig3)

    st.markdown("</div>", unsafe_allow_html=True)

elif (
    not st.session_state.error_message
):  # Показываем приветствие, только если нет ошибки и нет README
    st.info(
        "👋 Добро пожаловать! "
        "Введите URL GitHub репозитория в панели слева и выберите нужное действие."
    )
    st.markdown(
        f"""
    #### 🚀 Доступные функции:

    **✨ Сгенерировать README** - создание нового README файла с нуля:
    1.  Загрузка файлов из вашего репозитория.
    2.  Анализ структуры кода (AST).
    3.  Генерация описаний и структуры документации с помощью LLM.
    4.  Готовый <span class="lamoda-lime-text">`README.md`</span> для вас!

    **🔄 Обновить README** - актуализация существующего README:
    1.  Проверка наличия README в репозитории.
    2.  Анализ последних merged Pull Request'ов.
    3.  Если нет новых PR - уведомление о том, что обновление не требуется.
    4.  Сравнение с текущим состоянием проекта.
    5.  Умное обновление документации только при необходимости.
    """
    )

# Подвал
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
