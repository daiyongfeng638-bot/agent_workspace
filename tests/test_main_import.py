from importlib import import_module


def test_src_main_import_exposes_callable_main():
    module = import_module("src.main")

    assert hasattr(module, "main")
    assert callable(module.main)
