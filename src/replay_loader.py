"""Replay case 加载与基础校验。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .config import BASE_DIR


REPLAY_CASES_DIR = BASE_DIR / "data" / "replay_cases"


class ReplayCaseError(ValueError):
    """Replay case 文件或内容不合法。"""

    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


def discover_replay_case_files(directory: Path | None = None) -> List[Path]:
    """发现 replay case 文件，按文件名排序。"""

    base_dir = directory or REPLAY_CASES_DIR
    if not base_dir.exists():
        return []
    return sorted((path for path in base_dir.glob("*.json") if path.is_file()), key=lambda path: path.name)


def _require_key(data: Dict[str, Any], key: str, path: Path) -> Any:
    if key not in data:
        raise ReplayCaseError(path, f"缺少顶层必要字段: {key}")
    return data[key]


def _ensure_dict(value: Any, path: Path, field_name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ReplayCaseError(path, f"{field_name} 必须是 dict")
    return value


def validate_replay_case(data: Dict[str, Any], path: Path) -> Dict[str, Any]:
    """校验 replay case 的最小结构。"""

    if not isinstance(data, dict):
        raise ReplayCaseError(path, "JSON 顶层必须是对象")

    case_id = _require_key(data, "case_id", path)
    position_state = _ensure_dict(_require_key(data, "position_state", path), path, "position_state")
    analysis_result = _ensure_dict(_require_key(data, "analysis_result", path), path, "analysis_result")
    _require_key(data, "last_exit_time", path)
    meta = _ensure_dict(_require_key(data, "meta", path), path, "meta")

    if "has_position" not in position_state:
        raise ReplayCaseError(path, "position_state 缺少必要字段: has_position")
    if "source" not in meta:
        raise ReplayCaseError(path, "meta 缺少必要字段: source")

    return {
        "case_id": case_id,
        "position_state": position_state,
        "analysis_result": analysis_result,
        "last_exit_time": data["last_exit_time"],
        "meta": meta,
    }


def load_replay_case(path: str | Path) -> Dict[str, Any]:
    """加载单个 replay case 文件并进行基础校验。"""

    case_path = Path(path)
    try:
        raw_text = case_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ReplayCaseError(case_path, f"读取失败: {exc}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ReplayCaseError(case_path, f"JSON 解析失败: {exc.msg} (line {exc.lineno}, column {exc.colno})") from exc

    return validate_replay_case(data, case_path)


def load_replay_cases(directory: Path | None = None) -> List[Dict[str, Any]]:
    """加载目录下全部 replay cases。"""

    return [load_replay_case(path) for path in discover_replay_case_files(directory)]