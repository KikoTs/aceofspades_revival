import ast
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "aoslib"
    / "scenes"
    / "frontend"
    / "listPanelBase.py"
)


def load_layout_method():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ListPanelBase"
    )
    method_node = next(
        node
        for node in class_node.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "set_list_items_position_on_scroll"
        )
    )
    module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace["set_list_items_position_on_scroll"]


class FakeRow:
    def __init__(self):
        self.enable_on_scroll = True
        self.enabled = None
        self.positions = []

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update_position(self, x, y, width, height, highlight_width):
        self.positions.append((x, y, width, height, highlight_width))


def test_scrolled_rows_are_translated_into_the_first_visible_slot():
    rows = [FakeRow() for _ in range(6)]
    panel = SimpleNamespace(
        rows=rows,
        min_index=2,
        max_index=5,
        row_height=30,
        line_spacing=4,
    )

    load_layout_method()(panel, 100, 400, 250)

    assert rows[2].positions[-1][1] == 400
    assert rows[3].positions[-1][1] == 366
    assert rows[4].positions[-1][1] == 332
    assert [row.enabled for row in rows] == [
        False,
        False,
        True,
        True,
        True,
        False,
    ]


def test_zero_scroll_keeps_the_original_row_positions():
    rows = [FakeRow() for _ in range(3)]
    panel = SimpleNamespace(
        rows=rows,
        min_index=0,
        max_index=3,
        row_height=20,
        line_spacing=5,
    )

    load_layout_method()(panel, 10, 200, 100)

    assert [row.positions[-1][1] for row in rows] == [200, 175, 150]
