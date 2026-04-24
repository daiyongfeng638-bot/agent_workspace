from importlib import import_module
from pathlib import Path


def test_readme_recommends_python_m_src_main():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    content = readme.read_text(encoding="utf-8")

    assert "python -m src.main" in content


def test_src_main_import_exposes_callable_main():
    module = import_module("src.main")

    assert hasattr(module, "main")
    assert callable(module.main)
