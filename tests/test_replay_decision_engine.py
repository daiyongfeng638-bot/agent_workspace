from datetime import datetime

from src.decision_engine import decide_action
from src.replay_loader import discover_replay_case_files, load_replay_case
from src.result_validator import normalize_open_signal_result, normalize_position_management_result


VALID_DECISION_ACTIONS = {"OPEN_ORDER", "WAIT", "HOLD_POSITION"}


def _normalize_analysis_result(analysis_result):
    action = str(analysis_result.get("action", "")).upper()
    if action in {"HOLD", "ADD", "EXIT", "REDUCE", "MOVE_SL"}:
        return normalize_position_management_result(analysis_result)
    return normalize_open_signal_result(analysis_result)


def _parse_last_exit_time(value):
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def test_replay_cases_decision_pipeline_produces_valid_decisions():
    for path in discover_replay_case_files():
        case = load_replay_case(path)
        normalized_analysis_result, _report = _normalize_analysis_result(case["analysis_result"])
        decision = decide_action(
            case["position_state"],
            normalized_analysis_result,
            _parse_last_exit_time(case["last_exit_time"]),
        )

        assert isinstance(decision, dict)
        assert "action" in decision
        assert "allowed" in decision
        assert "reason" in decision
        assert decision["action"] in VALID_DECISION_ACTIONS
        assert isinstance(decision["allowed"], bool)
        assert isinstance(decision["reason"], str)
        assert decision["reason"].strip()
