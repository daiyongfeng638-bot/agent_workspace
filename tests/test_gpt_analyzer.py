import src.gpt_analyzer as gpt_analyzer  # noqa: E402


def test_analyze_open_signal_without_api_key_returns_safe_mock(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = gpt_analyzer.analyze_open_signal([])
    assert result["signal"] == "NONE"
    assert result["confidence"] == 0
    assert "image_paths" in result["evidence"]


def test_parse_json_result_valid_json():
    data = gpt_analyzer._parse_json_result('{"signal":"LONG","confidence":88}')
    assert data["signal"] == "LONG"
    assert data["confidence"] == 88


def test_package_import_from_src_namespace():
    import src.gpt_analyzer as module

    assert hasattr(module, "analyze_open_signal")
