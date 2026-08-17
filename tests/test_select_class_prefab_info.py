import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT
    / "aoslib"
    / "scenes"
    / "ingame_menus"
    / "selectClass.py"
)


def load_draw_prefab_info():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SelectClass"
    )
    method_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "draw_prefab_info"
    )
    module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "FLAREBLOCK_TOOL": 22,
        "PREFAB_NAME_TYPES": (str,),
    }
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace["draw_prefab_info"]


def test_numeric_non_flare_prefab_does_not_crash_tooltip():
    draw_prefab_info = load_draw_prefab_info()

    # Regression for production traceback:
    # AttributeError: 'int' object has no attribute 'upper'
    assert draw_prefab_info(object(), None, 0, 0, 1000000024) is None
