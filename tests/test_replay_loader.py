from pathlib import Path

import pytest

from src.replay_loader import (
    ReplayCaseError,
    discover_replay_case_files,
    load_replay_case,
)


def test_discover_replay_case_files_is_sorted():
    files = discover_replay_case_files()

    names = [path.name for path in files]
    assert names == sorted(names)
    assert names == ["sample_case_01.json", "sample_case_02.json", "sample_case_03.json"]


def test_load_single_replay_case_success():
    case = load_replay_case(Path("data/replay_cases/sample_case_01.json"))

    assert case["case_id"] == "sample_case_01"
    assert case["position_state"]["has_position"] is False
    assert case["analysis_result"]["action"] == "BUY"
    assert case["meta"]["source"] == "replay"


def test_load_replay_case_invalid_json_raises_clear_error(tmp_path: Path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not-json}", encoding="utf-8")

    with pytest.raises(ReplayCaseError) as exc_info:
        load_replay_case(bad_file)

    message = str(exc_info.value)
    assert str(bad_file) in message
    assert "JSON 解析失败" in message


def test_load_replay_case_missing_field_raises_clear_error(tmp_path: Path):
    bad_file = tmp_path / "missing_meta.json"
    bad_file.write_text(
        '{"case_id":"x","position_state":{"has_position":false},"analysis_result":{},"last_exit_time":null}',
        encoding="utf-8",
    )

    with pytest.raises(ReplayCaseError) as exc_info:
        load_replay_case(bad_file)

    message = str(exc_info.value)
    assert str(bad_file) in message
    assert "缺少顶层必要字段: meta" in message


def test_load_replay_case_missing_case_id_raises_clear_error(tmp_path: Path):
    bad_file = tmp_path / "missing_case_id.json"
    bad_file.write_text(
        '{"position_state":{"has_position":false},"analysis_result":{},"last_exit_time":null,"meta":{"source":"replay"}}',
        encoding="utf-8",
    )

    with pytest.raises(ReplayCaseError) as exc_info:
        load_replay_case(bad_file)

    message = str(exc_info.value)
    assert str(bad_file) in message
    assert "缺少顶层必要字段: case_id" in message


def test_load_replay_case_missing_nested_field_raises_clear_error(tmp_path: Path):
    bad_file = tmp_path / "missing_nested.json"
    bad_file.write_text(
        '{"case_id":"x","position_state":{},"analysis_result":{},"last_exit_time":null,"meta":{"source":"replay"}}',
        encoding="utf-8",
    )

    with pytest.raises(ReplayCaseError) as exc_info:
        load_replay_case(bad_file)

    message = str(exc_info.value)
    assert str(bad_file) in message
    assert "position_state 缺少必要字段: has_position" in message


def test_load_replay_case_invalid_position_state_type_raises_clear_error(tmp_path: Path):
    bad_file = tmp_path / "invalid_position_state.json"
    bad_file.write_text(
        '{"case_id":"x","position_state":[],"analysis_result":{},"last_exit_time":null,"meta":{"source":"replay"}}',
        encoding="utf-8",
    )

    with pytest.raises(ReplayCaseError) as exc_info:
        load_replay_case(bad_file)

    message = str(exc_info.value)
    assert str(bad_file) in message
    assert "position_state 必须是 dict" in message