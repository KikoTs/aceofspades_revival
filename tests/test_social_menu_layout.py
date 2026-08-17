import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def module_constants(relative_path):
    source = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    values = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        expression = ast.Expression(node.value)
        try:
            values[target.id] = eval(
                compile(expression, relative_path, "eval"), {}, values
            )
        except (NameError, TypeError, ValueError):
            continue
    return values, source


def test_friends_menu_controls_do_not_overlap():
    values, _ = module_constants(
        "aoslib/scenes/frontend/friendsMenu.py"
    )

    tab_bottom = values["CONTENT_TOP"] - values["TAB_HEIGHT"]
    search_top = values["SEARCH_BOTTOM"] + values["SEARCH_HEIGHT"]
    list_bottom = values["LIST_TOP"] - values["LIST_HEIGHT"]

    assert tab_bottom > search_top
    assert values["SEARCH_BOTTOM"] > values["LIST_TOP"]
    assert list_bottom == values["CONTENT_BOTTOM"]


def test_friends_menu_columns_and_action_rows_are_aligned():
    values, _ = module_constants(
        "aoslib/scenes/frontend/friendsMenu.py"
    )

    assert values["LEFT_X"] + values["LEFT_WIDTH"] + 5 == values["RIGHT_X"]
    assert values["LEFT_WIDTH"] == values["RIGHT_WIDTH"]
    assert values["ACTION_WIDTH"] * 2 + 8 == values["RIGHT_WIDTH"] - 8


def test_main_menu_friends_button_uses_text_button_top_coordinate():
    _, source = module_constants(
        "aoslib/scenes/frontend/selectMenu.py"
    )

    assert "square_button_y + square_button_width / 2.0" in source
    assert "square_button_y - square_button_width / 2.0" not in source


def test_friends_dialog_is_the_topmost_menu_element():
    _, source = module_constants(
        "aoslib/scenes/frontend/friendsMenu.py"
    )

    assert source.index("self.primary_button = self.create_button") < source.index(
        "self.elements.append(self.message_box)"
    )
