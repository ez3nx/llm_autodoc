# app/ui.py
import sys
import os

# Добавляем корневую директорию проекта (на один уровень выше 'app') в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from dotenv import load_dotenv
from app.services.github_parser import GithubParser
from app.services.ast_analyzer import AstAnalyzer
from app.services.llm_agent import LlmAgent # Уже импортирован, все ок
from app.services.doc_generator import DocGenerator # Не используется в текущей логике README, но оставлен

load_dotenv() # Загружаем .env из корня проекта

# --- Новые корпоративные цвета Lamoda Tech ---
LAMODA_LIME_ACCENT = "#CDFE00"
LAMODA_BLACK_BG = "#000000"
LAMODA_WHITE_TEXT = "#FFFFFF"
LAMODA_BLACK_TEXT_ON_LIME = "#000000"
LAMODA_DARK_GRAY_SUBTLE = "#1A1A1A"
LAMODA_MID_GRAY_BORDER = "#333333"

st.set_page_config(
    page_title="AI AutoDoc Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
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
""", unsafe_allow_html=True)

# --- Инициализация сервисов ---
@st.cache_resource
def get_services():
    github_token = os.getenv("GITHUB_TOKEN_AUTODOC")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY") # Получаем ключ для OpenRouter

    if not github_token:
        st.sidebar.error("GITHUB_TOKEN_AUTODOC не найден в .env. Пожалуйста, добавьте его.")
        st.stop()
    
    # Ключ для LLM не является критичным для запуска самого UI,
    # но LLM функционал не будет работать без него.
    # LlmAgent сам выведет предупреждение в консоль, если ключ отсутствует.
    # Можно добавить st.sidebar.warning, если ключ не найден, но это опционально.
    if not openrouter_api_key:
        st.sidebar.warning("OPENROUTER_API_KEY не найден в .env. Генерация документации через LLM будет недоступна или вернет ошибку.")

    return {
        "github_parser": GithubParser(github_token=github_token),
        "ast_analyzer": AstAnalyzer(),
        "llm_agent": LlmAgent(openrouter_api_key=openrouter_api_key), # Используем правильный ключ
        "doc_generator": DocGenerator(template_dir="app/templates") # Оставлен, хотя не используется для README
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
st.markdown(f"""
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
""", unsafe_allow_html=True)

# Сайдбар для ввода данных
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 2.5rem; color: {LAMODA_LIME_ACCENT}; margin-bottom: 10px;">⚙️</div>
        <h2 style="font-weight: 600; font-size: 1.4rem;">Настройки проекта</h2>
    </div>
    """, unsafe_allow_html=True)
    
    repo_url = st.text_input(
        "🔗 URL GitHub репозитория",
        placeholder="https://github.com/owner/repository",
        help="Введите полный URL публичного GitHub репозитория."
    )

    # Опционально: выбор модели LLM
    # доступные_модели = list(LlmAgent.DEFAULT_MODEL_MAPPING.keys())
    # выбранная_модель_ключ = st.selectbox(
    #     "🤖 Выберите модель LLM",
    #     options=доступные_модели,
    #     index=доступные_модели.index(llm_agent.default_model_key) # Устанавливаем дефолтное значение из агента
    # )

    # Опционально: выбор стиля README
    # readme_style = st.selectbox(
    #     "🎨 Стиль README",
    #     options=["summary", "detailed"],
    #     index=0 # "summary" по умолчанию
    # )

    if st.button("✨ Сгенерировать README", type="secondary", use_container_width=True):
        if repo_url:
            st.session_state.generated_readme = None
            st.session_state.error_message = None
            try:
                with st.spinner("🚀 Магия ИИ в действии... Пожалуйста, подождите..."):
                    spinner_placeholder = st.empty()
                    
                    spinner_placeholder.text("1/4: Получение файлов из репозитория...")
                    files_content = github_parser.get_repo_files_content(repo_url)
                    if not files_content:
                        st.session_state.error_message = "Не удалось получить файлы или репозиторий пуст/недоступен."
                        spinner_placeholder.empty()
                        st.rerun()

                    spinner_placeholder.text("2/4: Анализ структуры кода (AST)...")
                    ast_data = ast_analyzer.analyze_repository(files_content)
                    
                    spinner_placeholder.text("3/4: Генерация описаний с помощью LLM...")
                    # Передаем выбранную модель и стиль, если добавили выбор в UI, иначе используются дефолтные
                    llm_output = llm_agent.generate_readme_content(
                        ast_data, 
                        files_content
                        # style=readme_style, # если есть выбор стиля
                        # model_key=выбранная_модель_ключ # если есть выбор модели
                    )

                    if llm_output.startswith("⚠️ Ошибка") or llm_output.startswith("# Ошибка"):
                        st.session_state.error_message = f"Ошибка от LLM: {llm_output}"
                        spinner_placeholder.empty()
                        st.rerun() # Перезапуск для отображения ошибки

                    spinner_placeholder.text("4/4: Формирование финального README.md...")
                    final_readme = llm_output
                    st.session_state.generated_readme = final_readme
                    
                    spinner_placeholder.empty()
                    st.success("🎉 Документация успешно сгенерирована!")

            except Exception as e:
                st.session_state.error_message = f"Произошла непредвиденная ошибка: {str(e)}"
                # st.exception(e) # Для детального трейсбека в UI, если нужно
                print(f"UI Error: {e}") # Логируем ошибку в консоль
                import traceback
                traceback.print_exc() # Печатаем полный трейсбек в консоль сервера
                if 'spinner_placeholder' in locals(): # Проверяем, существует ли переменная
                    spinner_placeholder.empty()
                st.rerun() # Перезапуск для отображения ошибки
        else:
            st.sidebar.warning("Пожалуйста, введите URL репозитория.")

# Основная область для вывода
if st.session_state.error_message:
    st.error(f"🚫 {st.session_state.error_message}") # Убрал "Ошибка:" т.к. оно может быть в самой error_message

if st.session_state.generated_readme:
    st.markdown("---")
    st.subheader("📄 Сгенерированный README.md")
    st.markdown(f"""
    <div class="readme-container">
    {st.session_state.generated_readme}
    </div>
    """, unsafe_allow_html=True)
    
    st.download_button(
        label="💾 Скачать README.md",
        data=st.session_state.generated_readme,
        file_name="README_generated.md",
        mime="text/markdown",
        use_container_width=True,
        type="secondary" # Это сделает кнопку акцентной по вашим стилям
    )
elif not st.session_state.error_message: # Показываем приветствие, только если нет ошибки и нет README
    st.info(
        "👋 Добро пожаловать! "
        "Введите URL GitHub репозитория в панели слева и нажмите 'Сгенерировать README'."
    )
    st.markdown(f"""
    #### Как это работает?
    1.  Загрузка файлов из вашего репозитория.
    2.  Анализ структуры кода (AST).
    3.  Генерация описаний и структуры документации с помощью LLM.
    4.  Готовый <span class="lamoda-lime-text">`README.md`</span> для вас!
    """)

# Подвал
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 1rem 0; font-size: 0.9rem; color: #777777;">
    Разработано с <span style="color: {LAMODA_LIME_ACCENT};">❤️</span> на хакатоне | <span class="logo-text-la">la</span><span class="logo-text-tech">tech</span> Inspired
</div>
""", unsafe_allow_html=True)