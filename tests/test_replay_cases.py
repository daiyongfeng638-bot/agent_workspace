from src.result_validator import normalize_open_signal_result, normalize_position_management_result
from src.replay_loader import discover_replay_case_files, load_replay_case


REPLAY_CASE_PATHS = discover_replay_case_files()


def _normalize_analysis_result(analysis_result):
    action = str(analysis_result.get("action", "")).upper()
    if action in {"HOLD", "ADD", "EXIT", "REDUCE", "MOVE_SL"}:
        return normalize_position_management_result(analysis_result)
    return normalize_open_signal_result(analysis_result)


def test_replay_cases_can_all_be_loaded():
    cases = [load_replay_case(path) for path in REPLAY_CASE_PATHS]

    assert len(cases) >= 3
    assert [case["case_id"] for case in cases] == [path.stem for path in REPLAY_CASE_PATHS]


def test_replay_cases_analysis_results_validate_successfully():
    for path in REPLAY_CASE_PATHS:
        case = load_replay_case(path)
        result, report = _normalize_analysis_result(case["analysis_result"])

        assert isinstance(result, dict)
        assert result["action"]
        assert isinstance(report.summary(), str)
        assert report.message