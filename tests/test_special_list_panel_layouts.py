import ast
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def load_method(relative_path, class_name, globals_=None):
    module_path = PROJECT_ROOT / relative_path
    module = ast.parse(
        extract_method_source(
            module_path,
            class_name,
            "set_list_items_position_on_scroll",
        )
    )
    namespace = {"xrange": range}
    namespace.update(globals_ or {})
    exec(compile(module, str(module_path), "exec"), namespace)
    return namespace["set_list_items_position_on_scroll"]


class FakeRow:
    def __init__(self):
        self.enable_on_scroll = True
        self.enabled = None
        self.visible = True
        self.positions = []

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update_position(self, x, y, width, height, highlight_width):
        self.positions.append((x, y, width, height, highlight_width))


class FakeCategoryRow(FakeRow):
    def __init__(self):
        super().__init__()
        self.spacing_colour = None
        self.spacing_updates = []

    def enable_draw_spacing(self, enabled, *args):
        self.spacing_updates.append((enabled, args))


def test_expandable_settings_rows_move_and_hidden_rows_stay_hidden():
    rows = [
        FakeCategoryRow(),
        FakeRow(),
        FakeRow(),
        FakeCategoryRow(),
        FakeRow(),
    ]

    def get_row_height(row):
        return 40 if type(row) is FakeCategoryRow else 30

    panel = SimpleNamespace(
        rows=rows,
        min_index=2,
        max_index=5,
        line_spacing=4,
        category_spacing_colour=(0, 0, 0, 0),
        category_row_spacing=2,
        get_row_height=get_row_height,
    )
    method = load_method(
        Path("aoslib/scenes/frontend/expandableListPanel.py"),
        "ExpandableListPanel",
        {"CategoryListItem": FakeCategoryRow},
    )

    method(panel, 100, 400, 250)

    assert rows[2].positions[-1][1] == 400
    assert rows[3].positions[-1][1] == 356
    assert rows[4].positions[-1][1] == 322
    assert [row.enabled for row in rows] == [False, False, True, True, True]
    assert [row.visible for row in rows] == [False, False, True, True, True]


def test_leaderboard_rows_move_beneath_the_fixed_header():
    rows = [FakeRow() for _ in range(7)]
    panel = SimpleNamespace(
        rows=rows,
        min_index=2,
        max_index=6,
        row_height=30,
        line_spacing=4,
        top_padding=5,
    )
    method = load_method(
        Path("aoslib/scenes/frontend/leaderboardListPanel.py"),
        "LeaderboardListPanel",
    )

    method(panel, 100, 400, 250)

    assert rows[2].positions[-1][1] == 365
    assert rows[3].positions[-1][1] == 331
    assert rows[4].positions[-1][1] == 297


def test_profile_rows_move_while_summary_row_remains_pinned():
    rows = [FakeRow() for _ in range(7)]
    panel = SimpleNamespace(
        rows=rows,
        min_index=2,
        max_index=6,
        row_height=30,
        line_spacing=4,
        first_item_y_offset=10,
    )
    method = load_method(
        Path("aoslib/scenes/frontend/playerProfileMenu.py"),
        "PlayerProfileSummaryListPanel",
    )

    method(panel, 100, 400, 250)

    assert rows[0].positions[-1][1] == 410
    assert rows[3].positions[-1][1] == 366
    assert rows[4].positions[-1][1] == 332
    assert rows[5].positions[-1][1] == 298
