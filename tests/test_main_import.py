from importlib import import_module
import ast
from pathlib import Path


def test_readme_recommends_python_m_src_main():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    content = readme.read_text(encoding="utf-8")

    assert "python -m src.main" in content


def test_readme_dry_run_safety_boundary_matches_order_filler_default():
    root = Path(__file__).resolve().parent.parent

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "默认不自动提交订单" in readme
    assert "dry_run=True" in readme

    order_filler_source = (root / "src" / "order_filler.py").read_text(encoding="utf-8-sig")
    module = ast.parse(order_filler_source)
    fill_order = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "fill_order"
    )

    assert fill_order.args.defaults, "fill_order should define a default for dry_run"
    dry_run_default = fill_order.args.defaults[-1]
    assert isinstance(dry_run_default, ast.Constant)
    assert dry_run_default.value is True


def test_src_main_import_exposes_callable_main():
    module = import_module("src.main")

    assert hasattr(module, "main")
    assert callable(module.main)
