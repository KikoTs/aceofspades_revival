import ast
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT
    / "aoslib"
    / "scenes"
    / "frontend"
    / "baseSquadsMenu.py"
)


def load_method(name, globals_dict):
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BaseSquadsMenu"
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


class FakeSquadEventManager:
    on_data_changed = object()

    def __init__(self):
        self.unregister_count = 0

    def unregister_callback(self, event, callback):
        self.unregister_count += 1


def make_stoppable_menu(callback):
    return SimpleNamespace(
        auto_data_refresh_callback=callback,
        auto_data_refresh_enabled=True,
        server_type_filter=SimpleNamespace(get_selected_index=lambda: 1),
        list_panel=SimpleNamespace(get_selected_item=lambda: None),
        on_data_changed=lambda *args: None,
    )


def test_on_stop_ignores_an_already_fired_delayed_call():
    delayed_call = FakeDelayedCall(active=False)
    event_manager = FakeSquadEventManager()
    on_stop = load_method("on_stop", {"squadEventMgr": event_manager})
    menu = make_stoppable_menu(delayed_call)

    on_stop(menu)

    assert delayed_call.cancel_count == 0
    assert menu.auto_data_refresh_callback is None
    assert menu.auto_data_refresh_enabled is False
    assert event_manager.unregister_count == 1


def test_on_stop_cancels_an_active_call_and_is_repeatable():
    delayed_call = FakeDelayedCall(active=True)
    event_manager = FakeSquadEventManager()
    on_stop = load_method("on_stop", {"squadEventMgr": event_manager})
    menu = make_stoppable_menu(delayed_call)

    on_stop(menu)
    on_stop(menu)

    assert delayed_call.cancel_count == 1
    assert menu.auto_data_refresh_callback is None
    assert event_manager.unregister_count == 2


def test_refresh_does_not_reschedule_after_transition_starts():
    scheduled = []
    reactor = SimpleNamespace(
        callLater=lambda *args: scheduled.append(args),
    )
    on_auto_data_refresh = load_method(
        "on_auto_data_refresh",
        {
            "reactor": reactor,
            "SteamRefreshLobbyData": lambda lobby_id: None,
        },
    )
    menu = SimpleNamespace(
        auto_data_refresh_callback=FakeDelayedCall(active=False),
        auto_data_refresh_enabled=True,
    )

    def stop_during_refresh():
        menu.auto_data_refresh_enabled = False

    menu.on_refresh = stop_during_refresh

    on_auto_data_refresh(menu)

    assert scheduled == []
    assert menu.auto_data_refresh_callback is None


def test_refresh_reschedules_while_menu_is_active():
    scheduled = []
    next_call = FakeDelayedCall(active=True)

    def call_later(*args):
        scheduled.append(args)
        return next_call

    on_auto_data_refresh = load_method(
        "on_auto_data_refresh",
        {
            "reactor": SimpleNamespace(callLater=call_later),
            "SteamRefreshLobbyData": lambda lobby_id: None,
        },
    )
    menu = SimpleNamespace(
        auto_data_refresh_callback=FakeDelayedCall(active=False),
        auto_data_refresh_enabled=True,
        on_refresh=lambda: None,
        on_auto_data_refresh=lambda: None,
        list_panel=SimpleNamespace(
            rows=[],
            get_selected_item=lambda: None,
        ),
    )

    on_auto_data_refresh(menu)

    assert len(scheduled) == 1
    assert scheduled[0][0] == 1.0
    assert menu.auto_data_refresh_callback is next_call
