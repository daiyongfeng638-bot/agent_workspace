import importlib
import sys


def _import_gpt_analyzer(tmp_path, monkeypatch):
    import src.logger as logger

    monkeypatch.setattr(logger, "log_message", lambda *args, **kwargs: str(tmp_path / "app.log"))
    monkeypatch.setattr(logger, "save_analysis_result", lambda data: str(tmp_path / "analysis.json"))
    sys.modules.pop("src.prompts", None)
    sys.modules.pop("src.gpt_analyzer", None)
    module = importlib.import_module("src.gpt_analyzer")
    monkeypatch.setattr(module, "_has_api_key", lambda: False)
    return module


def test_analyze_open_signal_without_api_key_returns_safe_mock(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    gpt_analyzer = _import_gpt_analyzer(tmp_path, monkeypatch)
    result = gpt_analyzer.analyze_open_signal([])
    assert result["signal"] == "NONE"
    assert result["confidence"] == 0
    assert "image_paths" in result["evidence"]


def test_parse_json_result_valid_json():
    import src.gpt_analyzer as gpt_analyzer

    data = gpt_analyzer._parse_json_result('{"signal":"LONG","confidence":88}')
    assert data["signal"] == "LONG"
    assert data["confidence"] == 88


def test_package_import_from_src_namespace():
    import src.gpt_analyzer as module

    assert hasattr(module, "analyze_open_signal")