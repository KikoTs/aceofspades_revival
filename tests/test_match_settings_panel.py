import ast
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "aoslib"
    / "scenes"
    / "frontend"
    / "matchSettingsPanel.py"
)


def load_method(name, globals_dict):
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MatchSettingsPanel"
    )
    method_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = dict(globals_dict)
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace[name]


class FakeRow:
    def __init__(self, settings_id):
        self.settings_id = settings_id


class FakeListPanel:
    def __init__(self):
        self.rows = []
        self.scroll_calls = []
        self.scrollbar = SimpleNamespace(
            scroll_pos=0,
            set_scroll=lambda value: self.scroll_calls.append(value),
        )

    def on_scroll(self, value, silent=False):
        self.scroll_calls.append((value, silent))


def make_populate_panel(lobby_type):
    list_panel = FakeListPanel()
    panel = SimpleNamespace(
        lobby_id=7,
        list_panel=list_panel,
        manager=SimpleNamespace(media=object()),
        enable_privacy_type=False,
        enable_playlist=True,
        enable_max_players=True,
        enable_match_length=True,
        enable_map_rotation=True,
        enable_game_rules=True,
        enable_prefab_set=False,
        enable_ugc_mode=False,
        enable_save_map_name=False,
        last_scroll_index=None,
        on_max_players_changed=lambda value: None,
        on_match_length_changed=lambda value: None,
        on_local_setting_changed=lambda value=None: None,
        open_edit_game_rules_menu=lambda: None,
    )
    panel.add_playlist_row = lambda: list_panel.rows.append(FakeRow("PLAYLIST"))
    panel.add_map_rotation_row = lambda: list_panel.rows.append(
        FakeRow("MAP_ROTATION_FILENAME")
    )
    lobby_data = {"LobbyType": str(lobby_type)}
    return panel, lobby_data


def run_populate(lobby_type):
    match_lobby_type = 42
    panel, lobby_data = make_populate_panel(lobby_type)

    def get_lobby_data(lobby_id, key):
        assert lobby_id == 7
        return lobby_data.get(key, "")

    def set_lobby_data(key, value):
        lobby_data[key] = value

    def slider_row(display_name, settings_id, *args, **kwargs):
        return FakeRow(settings_id)

    def menu_row(display_name, settings_id, *args, **kwargs):
        return FakeRow(settings_id)

    local_host = SimpleNamespace(
        DEFAULT_SERVER_PORT=27015,
        BOT_COUNT_PRESETS=("0", "2", "4"),
        BOT_DIFFICULTIES=("easy", "mixed", "hard"),
        create_server_port_row=lambda *args, **kwargs: FakeRow("SERVER_PORT"),
    )
    populate = load_method(
        "populate_match_settings_list",
        {
            "SteamGetLobbyData": get_lobby_data,
            "SteamSetLobbyData": set_lobby_data,
            "MatchSettingsSliderListItem": slider_row,
            "MatchSettingsMenuListItem": menu_row,
            "MatchSettingsEditTextListItem": lambda *args, **kwargs: FakeRow(
                "MAP_TITLE"
            ),
            "get_display_name": lambda settings_id, lobby_id: "Default",
            "strings": SimpleNamespace(
                PRIVACY="Privacy",
                MAX_PLAYERS="Max Players",
                MATCH_LENGTH="Match Length",
                GAME_RULES="Game Rules",
                PREFAB_SET="Prefab Set",
                UGC_MAP_TITLE="Map Title",
            ),
            "PRIVACY_TYPES_LIST": (),
            "A2664": match_lobby_type,
            "A2668": (),
            "A2669": (),
            "local_host": local_host,
        },
    )
    populate(panel)
    return [row.settings_id for row in panel.list_panel.rows]


def test_normal_match_keeps_map_and_rules_before_optional_host_controls():
    rows = run_populate(42)

    assert rows == [
        "PLAYLIST",
        "MAX_PLAYERS",
        "MATCH_LENGTH",
        "MAP_ROTATION_FILENAME",
        "GAME_RULES",
        "BOT_COUNT",
        "BOT_DIFFICULTY",
        "SERVER_PORT",
    ]


def test_ugc_settings_do_not_receive_match_bot_or_port_rows():
    rows = run_populate(41)

    assert rows == [
        "PLAYLIST",
        "MAX_PLAYERS",
        "MATCH_LENGTH",
        "MAP_ROTATION_FILENAME",
        "GAME_RULES",
    ]


def test_mouse_wheel_scrolls_visible_settings_even_over_scrollbar():
    calls = []
    scrollbar = SimpleNamespace(
        scroll_pos=1,
        set_scroll=lambda value: calls.append(value),
    )
    list_panel = SimpleNamespace(
        scrollbar=scrollbar,
        get_mouse_collides=lambda x, y, include_scrollbar=False: include_scrollbar,
    )
    panel = SimpleNamespace(
        enabled=True,
        visible=True,
        visible_content=True,
        list_panel=list_panel,
    )
    on_mouse_scroll = load_method("on_mouse_scroll", {})

    on_mouse_scroll(panel, 10, 20, 0, -1)

    assert calls == [2]


def test_hidden_settings_panel_ignores_mouse_wheel():
    calls = []
    panel = SimpleNamespace(
        enabled=True,
        visible=True,
        visible_content=False,
        list_panel=SimpleNamespace(
            scrollbar=SimpleNamespace(
                scroll_pos=1,
                set_scroll=lambda value: calls.append(value),
            ),
            get_mouse_collides=lambda *args, **kwargs: True,
        ),
    )
    on_mouse_scroll = load_method("on_mouse_scroll", {})

    on_mouse_scroll(panel, 10, 20, 0, -1)

    assert calls == []
