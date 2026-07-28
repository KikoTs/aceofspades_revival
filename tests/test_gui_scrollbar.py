import ast
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from revival_scroll import consume_wheel_steps


MODULE_PATH = PROJECT_ROOT / "aoslib" / "gui.py"


def extract_method_source(module_path, class_name, method_name):
    lines = module_path.read_text(encoding="utf-8").splitlines()
    class_start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("class %s(" % class_name)
    )
    method_start = next(
        index
        for index in range(class_start + 1, len(lines))
        if lines[index].startswith("    def %s(" % method_name)
    )
    method_end = len(lines)
    for index in range(method_start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith("        "):
            method_end = index
            break
    return "\n".join(line[4:] for line in lines[method_start:method_end]) + "\n"


def load_vertical_scroll_method():
    module = ast.parse(
        extract_method_source(
            MODULE_PATH,
            "VerticalScrollBar",
            "on_mouse_scroll",
        )
    )
    namespace = {"consume_wheel_steps": consume_wheel_steps}
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace["on_mouse_scroll"]


class FakeScrollBar:
    def __init__(self, position=0):
        self.enabled = True
        self.focus = True
        self.scroll_pos = position
        self.positions = []

    def set_scroll(self, value):
        self.scroll_pos = value
        self.positions.append(value)


def test_vertical_scrollbar_moves_once_per_wheel_notch():
    scrollbar = FakeScrollBar(position=3)

    load_vertical_scroll_method()(scrollbar, 0, 0, 0, -1)

    assert scrollbar.positions == [4]


def test_vertical_scrollbar_accumulates_precision_wheel_packets():
    scrollbar = FakeScrollBar(position=3)
    on_mouse_scroll = load_vertical_scroll_method()

    for _ in range(4):
        on_mouse_scroll(scrollbar, 0, 0, 0, 0.25)

    assert scrollbar.positions == [2]


def test_vertical_scrollbar_preserves_multi_notch_events():
    scrollbar = FakeScrollBar(position=5)

    load_vertical_scroll_method()(scrollbar, 0, 0, 0, 3)

    assert scrollbar.positions == [2]
