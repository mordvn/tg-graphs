import os
import sys
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import (
    create_uploaded_file_from_path,
    get_module_name_from_path,
    load_and_run_plugin,
)


class TestCreateUploadedFileFromPath:
    def test_creates_bytesio_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write("test content")
            tmp_path = tmp.name

        try:
            result = create_uploaded_file_from_path(tmp_path)

            assert isinstance(result, io.BytesIO)
            assert result.name == os.path.basename(tmp_path)
            assert result.full_path == tmp_path
            assert result.read() == b"test content"
        finally:
            os.unlink(tmp_path)

    def test_handles_binary_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"\x00\x01\x02\x03")
            tmp_path = tmp.name

        try:
            result = create_uploaded_file_from_path(tmp_path)
            assert result.read() == b"\x00\x01\x02\x03"
        finally:
            os.unlink(tmp_path)


class TestGetModuleNameFromPath:
    def test_generates_module_name_from_path(self):
        path = "/some/path/to/plugin.py"
        module_name = get_module_name_from_path(path)

        assert module_name.startswith("plugin_")
        assert "plugin" in module_name  # plugin name should be in the result
        assert len(module_name) > len("plugin_plugin")  # Should include hash

    def test_same_path_generates_same_name(self):
        path = "/some/path/to/plugin.py"
        name1 = get_module_name_from_path(path)
        name2 = get_module_name_from_path(path)

        assert name1 == name2

    def test_different_paths_generate_different_names(self):
        path1 = "/some/path/to/plugin1.py"
        path2 = "/some/path/to/plugin2.py"
        name1 = get_module_name_from_path(path1)
        name2 = get_module_name_from_path(path2)

        assert name1 != name2


class TestLoadAndRunPlugin:
    def test_loads_and_runs_plugin_successfully(self):
        plugin_content = """
def run_plugin(data):
    pass
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp:
            tmp.write(plugin_content)
            tmp_path = tmp.name

        try:
            test_data = {"messages": [], "name": "Test Chat"}

            with patch("main.st") as _mock_st:
                load_and_run_plugin(tmp_path, test_data)

                # Should not raise any errors
                assert True
        finally:
            os.unlink(tmp_path)

    def test_handles_missing_function_gracefully(self):
        plugin_content = """
# Plugin without run_plugin function
def some_other_function():
    pass
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp:
            tmp.write(plugin_content)
            tmp_path = tmp.name

        try:
            test_data = {"messages": [], "name": "Test Chat"}

            with patch("main.st") as mock_st:
                load_and_run_plugin(tmp_path, test_data)

                # Should call st.error for missing function
                mock_st.error.assert_called()
                assert (
                    "не найдена" in mock_st.error.call_args[0][0].lower()
                    or "not found" in mock_st.error.call_args[0][0].lower()
                )
        finally:
            os.unlink(tmp_path)

    def test_handles_plugin_execution_error(self):
        plugin_content = """
def run_plugin(data):
    raise ValueError("Test error")
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp:
            tmp.write(plugin_content)
            tmp_path = tmp.name

        try:
            test_data = {"messages": [], "name": "Test Chat"}

            with patch("main.st") as mock_st:
                load_and_run_plugin(tmp_path, test_data)

                # Should call st.error for execution error
                mock_st.error.assert_called()
        finally:
            os.unlink(tmp_path)

    def test_handles_invalid_plugin_path(self):
        invalid_path = "/nonexistent/path/plugin.py"
        test_data = {"messages": [], "name": "Test Chat"}

        with patch("main.st") as mock_st:
            load_and_run_plugin(invalid_path, test_data)

            # Should call st.error for invalid path
            mock_st.error.assert_called()
