import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import io
import streamlit as st

video_path = os.path.join(os.path.dirname(__file__), "..", "images", "instruction.mp4")
plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")

# Организация плагинов по категориям
PLUGIN_CATEGORIES = {
    "📊 Основные": {
        "path": plugins_dir,
        "plugins": [
            ("hourly_activity.py", "Активность по часам"),
            ("messages_counter.py", "Счётчик сообщений"),
            ("radio_silence.py", "Паузы в общении"),
            ("reactions_per_user.py", "Реакции"),
            ("reply_network.py", "Сеть ответов"),
        ]
    },
    "💕 Girlfriend Research": {
        "path": os.path.join(plugins_dir, "girlfriend_research"),
        "plugins": [
            ("relationship_summary.py", "📋 Итоговый анализ"),
            ("deep_analysis.py", "🔬 Глубокий анализ (улучшенный)"),
            ("emotional_balance.py", "💚 Эмоциональный баланс"),
            ("initiative_ratio.py", "💬 Инициатива"),
            ("response_time.py", "⏱️ Время ответа"),
            ("toxicity_detector.py", "🔍 Токсичность"),
            ("complaint_meter.py", "😩 Жалобы"),
            ("support_balance.py", "🤝 Поддержка"),
            ("interest_reciprocity.py", "❓ Интерес"),
            ("message_length_balance.py", "📏 Длина сообщений"),
            ("attachment_style.py", "🧠 Тип привязанности"),
            ("love_language.py", "💕 Языки любви"),
        ]
    },
    "👥 Friend Research": {
        "path": os.path.join(plugins_dir, "friend_research"),
        "plugins": [
            ("friendship_balance.py", "⚖️ Баланс дружбы"),
            ("group_dynamics.py", "👥 Динамика группы"),
            ("activity_patterns.py", "📈 Паттерны активности"),
            ("contribution_score.py", "🏆 Вклад в общение"),
            ("topic_analysis.py", "💬 Анализ тем"),
        ]
    },
    "🔞 OnlyFans Research": {
        "path": os.path.join(plugins_dir, "girlfriend_research_onlyfans"),
        "plugins": [
            ("ovulation_detector.py", "🌡️ Детектор овуляции"),
            ("horny_meter.py", "🔥 Horny Meter"),
            ("sex_islands.py", "🏝️ Острова секса"),
            ("sexting_analyzer.py", "📱 Анализ секстинга"),
            ("desire_dynamics.py", "💋 Динамика желания"),
            ("flirt_style.py", "😏 Стиль флирта"),
            ("intimacy_calendar.py", "📅 Календарь интимности"),
        ]
    },
}


def create_uploaded_file_from_path(path):
    with open(path, "rb") as f:
        content = f.read()
    bytes_io = io.BytesIO(content)
    bytes_io.name = os.path.basename(path)
    bytes_io.full_path = path
    return bytes_io


st.set_page_config(page_title="Chat Analyzer", layout="wide")

# Sidebar: Load Chats
with st.sidebar.expander("📁 Загрузить чаты", expanded=True):
    uploaded_chats = st.file_uploader(
        "Загрузить чат в формате JSON",
        type=["json"],
        accept_multiple_files=True,
        key="chats_uploader",
        label_visibility="collapsed",
    )
    if uploaded_chats and not isinstance(uploaded_chats, list):
        uploaded_chats = [uploaded_chats]

# Sidebar: Plugin Categories with checkboxes
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 Плагины")

# Store selected plugins in session state
if "selected_plugins" not in st.session_state:
    st.session_state.selected_plugins = {}

selected_plugin_paths = []

for category_name, category_data in PLUGIN_CATEGORIES.items():
    category_path = category_data["path"]
    
    # Skip if category folder doesn't exist
    if not os.path.exists(category_path):
        continue
    
    with st.sidebar.expander(category_name, expanded=False):
        # Select all / Deselect all
        col1, col2 = st.columns(2)
        select_all_key = f"select_all_{category_name}"
        
        # Get available plugins in this category
        available_plugins = []
        for filename, label in category_data["plugins"]:
            plugin_path = os.path.join(category_path, filename)
            if os.path.exists(plugin_path):
                available_plugins.append((filename, label, plugin_path))
        
        if not available_plugins:
            st.caption("Нет плагинов в этой категории")
            continue
        
        with col1:
            if st.button("✅ Все", key=f"all_{category_name}", use_container_width=True):
                for filename, _, _ in available_plugins:
                    st.session_state.selected_plugins[f"{category_name}_{filename}"] = True
                st.rerun()
        
        with col2:
            if st.button("❌ Очистить", key=f"none_{category_name}", use_container_width=True):
                for filename, _, _ in available_plugins:
                    st.session_state.selected_plugins[f"{category_name}_{filename}"] = False
                st.rerun()
        
        # Individual plugin checkboxes
        for filename, label, plugin_path in available_plugins:
            key = f"{category_name}_{filename}"
            # Default to False (disabled)
            default_value = st.session_state.selected_plugins.get(key, False)
            
            if st.checkbox(label, value=default_value, key=f"cb_{key}"):
                st.session_state.selected_plugins[key] = True
                selected_plugin_paths.append(plugin_path)
            else:
                st.session_state.selected_plugins[key] = False

# Custom plugins upload
with st.sidebar.expander("📎 Свои плагины"):
    uploaded_plugins = st.file_uploader(
        "Загрузить плагины",
        type=["py"],
        accept_multiple_files=True,
        key="plugins_uploader",
        label_visibility="collapsed",
    )
    if uploaded_plugins and not isinstance(uploaded_plugins, list):
        uploaded_plugins = [uploaded_plugins]
    if not uploaded_plugins:
        uploaded_plugins = []

# Chat selection
st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 Чаты")
selected_file = None
data = None

if uploaded_chats:
    file_names = [file.name for file in uploaded_chats]
    selected_name = st.sidebar.selectbox("Выбрать чат", file_names)

    for file in uploaded_chats:
        if file.name == selected_name:
            selected_file = file
            break

    if selected_file:
        try:
            data = json.load(selected_file)
        except Exception as e:
            st.sidebar.error(f"Ошибка загрузки JSON: {e}")
else:
    st.sidebar.info("Загрузите файл чата")
    st.title("Telegram Chat Analyzer")
    
    st.markdown("""
    ### Как использовать:
    1. Экспортируйте чат из Telegram Desktop (JSON формат)
    2. Загрузите файл в боковой панели
    3. Выберите нужные плагины
    4. Анализируйте!
    
    ### Доступные категории плагинов:
    - **📊 Основные** — базовая статистика чата
    - **💕 Girlfriend Research** — анализ романтических отношений
    - **👥 Friend Research** — анализ дружеского общения
    """)
    
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode()

        video_html = f"""
            <video width="100%" autoplay loop muted controls>
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                Your browser does not support video tag.
            </video>
        """
        st.markdown(video_html, unsafe_allow_html=True)


def get_module_name_from_path(plugin_path: str) -> str:
    plugin_name = os.path.basename(plugin_path).replace(".py", "")
    plugin_hash = hashlib.md5(plugin_path.encode()).hexdigest()[:8]
    return f"plugin_{plugin_name}_{plugin_hash}"


def load_and_run_plugin(plugin_path: str, data, function_name="run_plugin"):
    module_name = get_module_name_from_path(plugin_path)

    if module_name in sys.modules:
        plugin_module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None:
            st.error("Не удалось создать спецификацию плагина.")
            return
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin_module
        try:
            spec.loader.exec_module(plugin_module)
        except Exception as e:
            st.error(f"Ошибка загрузки модуля: {e}")
            return

    if hasattr(plugin_module, function_name):
        func = getattr(plugin_module, function_name)
        try:
            func(data)
        except Exception as e:
            st.error(f"Ошибка плагина: {e}")
    else:
        st.error(f"Функция {function_name} не найдена в плагине")


# Run selected plugins
if data:
    # Show chat info
    chat_name = data.get("name", "Неизвестный чат")
    messages_count = len(data.get("messages", []))
    st.title(f"📊 {chat_name}")
    st.caption(f"Всего сообщений: {messages_count}")
    
    # Count selected plugins
    total_selected = len(selected_plugin_paths) + len(uploaded_plugins)
    
    if total_selected == 0:
        st.info("👈 Выберите плагины в боковой панели для анализа")
    else:
        st.markdown(f"**Выбрано плагинов: {total_selected}**")
        st.markdown("---")
        
        # Run predefined plugins
        for plugin_path in selected_plugin_paths:
            plugin_name = os.path.basename(plugin_path).replace(".py", "").replace("_", " ").title()
            with st.expander(f"📊 {plugin_name}", expanded=True):
                load_and_run_plugin(plugin_path, data)
        
        # Run custom uploaded plugins
        for plugin in uploaded_plugins:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
                tmp_file.write(plugin.read())
                tmp_file_path = tmp_file.name
            with st.expander(f"📎 {plugin.name}", expanded=True):
                load_and_run_plugin(tmp_file_path, data)

elif uploaded_chats:
    st.info("Выберите чат из списка")
