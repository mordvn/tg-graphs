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

predefined_plugin_paths = [
    os.path.join(os.path.dirname(__file__), "plugins", "hourly_activity.py"),
    os.path.join(os.path.dirname(__file__), "plugins", "messages_counter.py"),
    os.path.join(os.path.dirname(__file__), "plugins", "radio_silence.py"),
    os.path.join(os.path.dirname(__file__), "plugins", "reactions_per_user.py"),
    os.path.join(os.path.dirname(__file__), "plugins", "reply_network.py"),
]


def create_uploaded_file_from_path(path):
    with open(path, "rb") as f:
        content = f.read()
    # Create BytesIO to simulate file
    bytes_io = io.BytesIO(content)
    bytes_io.name = os.path.basename(path)
    return bytes_io


st.set_page_config(page_title="Chat Analyzer", layout="wide")

with st.sidebar.expander("Load Chats"):
    uploaded_chats = st.file_uploader(
        "Upload chat in JSON format",
        type=["json"],
        accept_multiple_files=True,
        key="chats_uploader",
        label_visibility="visible",
    )
    if uploaded_chats and not isinstance(uploaded_chats, list):
        uploaded_chats = [uploaded_chats]

with st.sidebar.expander("Plugins"):
    uploaded_plugins = st.file_uploader(
        "Upload plugins",
        type=["py"],
        accept_multiple_files=True,
        key="plugins_uploader",
        label_visibility="visible",
    )
    if uploaded_plugins and not isinstance(uploaded_plugins, list):
        uploaded_plugins = [uploaded_plugins]

for path in predefined_plugin_paths:
    if os.path.exists(path):
        uploaded_plugins.append(create_uploaded_file_from_path(path))

st.sidebar.title("Chats")
selected_file = None
data = None

if uploaded_chats:
    file_names = [file.name for file in uploaded_chats]
    selected_name = st.sidebar.selectbox("Select file", file_names)

    for file in uploaded_chats:
        if file.name == selected_name:
            selected_file = file
            break

    if selected_file:
        try:
            data = json.load(selected_file)
        except Exception as e:
            st.sidebar.error(f"JSON load error: {e}")
else:
    st.sidebar.warning("Upload a chat file first.")
    st.title("Telegram Chat Analyzer")
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
    # Generate unique name from path
    plugin_name = os.path.basename(plugin_path).replace(".py", "")
    plugin_hash = hashlib.md5(plugin_path.encode()).hexdigest()[:8]
    return f"plugin_{plugin_name}_{plugin_hash}"


def load_and_run_plugin(plugin_path: str, data, function_name="run_plugin"):
    module_name = get_module_name_from_path(plugin_path)

    # Check if module already loaded
    if module_name in sys.modules:
        plugin_module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None:
            st.error("Failed to create plugin spec.")
            return
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin_module
        try:
            spec.loader.exec_module(plugin_module)
        except Exception as e:
            st.error(f"Module load error: {e}")
            return

    if hasattr(plugin_module, function_name):
        func = getattr(plugin_module, function_name)
        try:
            func(data)
        except Exception as e:
            st.error(f"Plugin error: {e}")
    else:
        st.error(f"Function {function_name} not found in plugin")


if uploaded_plugins and data:
    for plugin in uploaded_plugins:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file.write(plugin.read())
            tmp_file_path = tmp_file.name
        st.subheader(f"Plugin: {plugin.name}")
        load_and_run_plugin(tmp_file_path, data)
elif uploaded_plugins and not data:
    st.warning("Plugin loaded but no chat selected.")
