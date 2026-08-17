import ast
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT
    / "aoslib"
    / "scenes"
    / "gui"
    / "horizontalListSelection.py"
)


def load_method(name):
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "HorizontalListSelection"
    )
    method_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"FLAREBLOCK_TOOL": 22}
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace[name]


class FakeButton:
    def __init__(self):
        self.image = None
        self.image_scale = None
        self.draw_background_image = False
        self.enabled = True
        self.border = False
        self.over = False

    def set_enabled(self, enabled):
        self.enabled = enabled

    def set_draw_border(self, enabled):
        self.border = enabled

    def on_mouse_motion(self, x, y, dx, dy):
        return


def make_selector(item_count=3, minimum_selected=0):
    selector = SimpleNamespace(
        _items=[],
        _items_per_page=item_count,
        _buttons=[FakeButton() for _ in range(item_count)],
        _item_index=[],
        _min_index=0,
        _min_selected_items=minimum_selected,
        _max_selected_items=1,
        _item_under_mouse=None,
        image_button_scale=1.0,
        draw_back_image=True,
        on_mouse_over_item_callback=None,
        _back_button=None,
        _next_button=None,
        fire_on_page_change_handler=lambda *args: None,
        fire_on_item_clicked_handler=lambda info: None,
        fire_on_mouse_over_handler=lambda info: None,
        update_navigation_buttons_state=lambda: None,
    )
    return selector


def test_missing_image_keeps_button_and_source_indices_aligned():
    populate = load_method("populate_items_list")
    on_item_selected = load_method("on_item_selected")
    clicked = []
    selector = make_selector()
    selector.fire_on_item_clicked_handler = clicked.append
    valid_image = object()

    populate(selector, [[999, None], ["prefab_valid", valid_image]])
    on_item_selected(selector, 1)

    assert selector._buttons[0].image is None
    assert selector._buttons[1].image is valid_image
    assert clicked[0]["id"] == "prefab_valid"
    assert clicked[0]["index"] == 1


def test_repopulating_reenables_items_without_an_explicit_enabled_flag():
    populate = load_method("populate_items_list")
    selector = make_selector(item_count=1)
    image = object()

    populate(selector, [["disabled", image, False]])
    assert selector._buttons[0].enabled is False

    populate(selector, [["normal", image]])
    assert selector._buttons[0].enabled is True


def test_required_selection_skips_items_without_images():
    populate = load_method("populate_items_list")
    selector = make_selector(minimum_selected=1)
    valid_image = object()

    populate(selector, [[999, None], ["prefab_valid", valid_image]])

    assert selector._item_index == [1]
    assert selector._buttons[0].border is False
    assert selector._buttons[1].border is True


def test_page_change_removes_a_stale_selection_without_an_image():
    populate = load_method("populate_items_list")
    selector = make_selector(item_count=1)
    selector._item_index = [0]

    populate(selector, [[999, None]], page_changed=True)

    assert selector._item_index == []
    assert selector._buttons[0].border is False
