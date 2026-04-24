from importlib.util import find_spec
from pathlib import Path


README_REPLAY_TEST_FILES = [
    Path("tests/test_replay_loader.py"),
    Path("tests/test_replay_cases.py"),
    Path("tests/test_replay_decision_engine.py"),
]

README_REPLAY_CASE_FILES = [
    Path("data/replay_cases/sample_case_01.json"),
    Path("data/replay_cases/sample_case_02.json"),
    Path("data/replay_cases/sample_case_03.json"),
]


def test_readme_replay_examples_reference_existing_files():
    for path in README_REPLAY_TEST_FILES:
        assert path.exists(), f"缺少 README 中引用的测试文件: {path}"

    for path in README_REPLAY_CASE_FILES:
        assert path.exists(), f"缺少 README 中引用的 replay 样例文件: {path}"


def test_readme_module_entry_src_main_is_importable():
    assert find_spec("src.main") is not None, "python -m src.main 所需模块不存在"
