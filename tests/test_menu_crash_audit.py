import ast
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def extract_method_source(relative_path, class_name, method_name):
    module_path = PROJECT_ROOT / relative_path
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
    return (
        module_path,
        "\n".join(line[4:] for line in lines[method_start:method_end]) + "\n",
    )


def load_method(relative_path, class_name, method_name, globals_=None):
    module_path, source = extract_method_source(
        relative_path,
        class_name,
        method_name,
    )
    namespace = dict(globals_ or {})
    exec(compile(ast.parse(source), str(module_path), "exec"), namespace)
    return namespace[method_name]


def extract_function_source(relative_path, function_name):
    module_path = PROJECT_ROOT / relative_path
    lines = module_path.read_text(encoding="utf-8").splitlines()
    function_start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("def %s(" % function_name)
    )
    function_end = len(lines)
    for index in range(function_start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith("    "):
            function_end = index
            break
    return module_path, "\n".join(lines[function_start:function_end]) + "\n"


def load_function(relative_path, function_name, globals_=None):
    module_path, source = extract_function_source(relative_path, function_name)
    namespace = dict(globals_ or {})
    exec(compile(ast.parse(source), str(module_path), "exec"), namespace)
    return namespace[function_name]


class FakeDelayedCall:
    def __init__(self, active):
        self.is_active = active
        self.cancel_count = 0

    def active(self):
        return self.is_active

    def cancel(self):
        if not self.is_active:
            raise AssertionError("an expired delayed call must not be cancelled")
        self.cancel_count += 1
        self.is_active = False


def make_lobby(callback):
    return SimpleNamespace(
        manager=object(),
        starting_game=True,
        start_game_tick_callback=callback,
        server_finder=None,
        start_game_button=None,
    )


def test_lobby_cancel_ignores_an_expired_delayed_call():
    stopped = []
    do_cancel_game = load_method(
        "aoslib/scenes/frontend/baseSquadLobbyMenu.py",
        "BaseSquadLobbyMenu",
        "do_cancel_game",
        {
            "local_host": SimpleNamespace(
                stop_active_session=lambda manager: stopped.append(manager)
            )
        },
    )
    delayed_call = FakeDelayedCall(active=False)
    menu = make_lobby(delayed_call)

    do_cancel_game(menu)

    assert delayed_call.cancel_count == 0
    assert menu.start_game_tick_callback is None
    assert menu.starting_game is False
    assert stopped == [menu.manager]


def test_lobby_cancel_cancels_an_active_delayed_call_once():
    do_cancel_game = load_method(
        "aoslib/scenes/frontend/baseSquadLobbyMenu.py",
        "BaseSquadLobbyMenu",
        "do_cancel_game",
        {
            "local_host": SimpleNamespace(
                stop_active_session=lambda manager: None
            )
        },
    )
    delayed_call = FakeDelayedCall(active=True)
    menu = make_lobby(delayed_call)

    do_cancel_game(menu)
    do_cancel_game(menu)

    assert delayed_call.cancel_count == 1
    assert menu.start_game_tick_callback is None


def test_ugc_disabled_class_path_uses_continue_statement():
    _, source = extract_method_source(
        "aoslib/scenes/ingame_menus/selectUGC.py",
        "SelectUGC",
        "on_start",
    )
    tree = ast.parse(source)

    assert any(isinstance(node, ast.Continue) for node in ast.walk(tree))
    assert not any(
        isinstance(node, ast.Name) and node.id == "contine"
        for node in ast.walk(tree)
    )


def test_select_team_uses_default_class_and_imports_statistics_menu():
    module_path = (
        PROJECT_ROOT / "aoslib/scenes/ingame_menus/selectTeam.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    loaded_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    imported_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "A553" not in loaded_names
    assert "DEFAULT_CLASS" in imported_names
    assert "ViewGameStats" in imported_names


def test_playlist_manager_draw_is_safe_to_call():
    draw = load_method(
        "aoslib/scenes/frontend/playlistUIManager.py",
        "PlayListUIManager",
        "draw",
    )

    assert draw(object()) is None


def test_leaderboard_stop_clears_only_the_leaderboard_callback():
    calls = []
    score_manager = SimpleNamespace(
        clear_request_leaderboard_callback=lambda: calls.append(
            "leaderboard"
        ),
        clear_request_profile_callback=lambda: calls.append("profile"),
    )
    on_stop = load_method(
        "aoslib/scenes/frontend/LeaderboardMenu.py",
        "LeaderboardMenu",
        "on_stop",
    )

    on_stop(SimpleNamespace(manager=SimpleNamespace(score_manager=score_manager)))

    assert calls == ["leaderboard"]


def test_block_tool_imports_math_for_bridge_distance():
    module_path = PROJECT_ROOT / "aoslib/weapons/blockToolCommon.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "math" in imported_names


def test_text_module_exports_the_runtime_input_ip_font_name():
    module_path = PROJECT_ROOT / "aoslib/text.py"
    source = module_path.read_text(encoding="utf-8")
    all_list_source = source[source.index("__all__ = "):]

    assert "'input_ip'" in all_list_source
    assert "'INPUT_IP'" not in all_list_source


def test_darker_colour_uses_all_base_colour_channels():
    get_darker_colour = load_function(
        "aoslib/common.py",
        "get_darker_colour",
    )

    assert get_darker_colour((100, 90, 80, 40), 25) == (75, 65, 55, 40)


class FakeImage:
    width = 100
    height = 60

    def __init__(self):
        self.anchor_x = 7
        self.anchor_y = 9
        self.blit_calls = []

    def blit(self, x, y):
        self.blit_calls.append((x, y, self.anchor_x, self.anchor_y))


class FakeGL:
    def glColor4f(self, *args):
        return

    def glPushMatrix(self):
        return

    def glTranslated(self, *args):
        return

    def glScaled(self, *args):
        return

    def glPopMatrix(self):
        return


def test_centered_scaled_image_draw_restores_original_anchors():
    draw_image_scaled = load_function(
        "aoslib/common.py",
        "draw_image_scaled",
        {"gl": FakeGL()},
    )
    image = FakeImage()

    draw_image_scaled(
        image,
        12,
        34,
        0.5,
        0.5,
        alignment="center",
        clear_colours=True,
    )

    assert image.blit_calls == [(0, 0, 50.0, 30.0)]
    assert (image.anchor_x, image.anchor_y) == (7, 9)
