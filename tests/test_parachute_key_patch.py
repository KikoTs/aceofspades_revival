import importlib.util
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "aoslib" / "parachute_key_patch.py"
SPEC = importlib.util.spec_from_file_location("client_parachute_key_patch", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
parachute_key_patch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parachute_key_patch)
PARACHUTE_NORMAL = parachute_key_patch.PARACHUTE_NORMAL
install = parachute_key_patch.install


class FakeWindow:
    def __init__(self):
        self._event_stack = [{"on_key_press": lambda symbol, modifiers: None}]

    def push_handlers(self, **handlers):
        self._event_stack.insert(0, handlers)


def manager_with_parachute(*, airborne=True, parachute=PARACHUTE_NORMAL):
    world_object = SimpleNamespace(airborne=airborne, hover=False)
    character = SimpleNamespace(world_object=world_object)
    player = SimpleNamespace(parachute=parachute, character=character)
    manager = SimpleNamespace(
        config=SimpleNamespace(hover=122),
        scene=SimpleNamespace(player=player),
        window=FakeWindow(),
    )
    return manager, world_object


def test_z_press_and_release_drive_existing_hover_bit():
    manager, world_object = manager_with_parachute()

    assert install(manager) is True
    press, release = manager._parachute_key_handlers
    press(122, 0)
    assert world_object.hover is True
    release(122, 0)
    assert world_object.hover is False


def test_parachute_cannot_deploy_on_ground_or_from_another_key():
    manager, world_object = manager_with_parachute(airborne=False)
    install(manager)
    press, _release = manager._parachute_key_handlers

    press(122, 0)
    assert world_object.hover is False
    world_object.airborne = True
    press(121, 0)
    assert world_object.hover is False


def test_install_is_idempotent_and_keeps_handler_reachable():
    manager, _world_object = manager_with_parachute()

    assert install(manager) is True
    handlers = manager._parachute_key_handlers
    assert install(manager) is False
    assert manager._parachute_key_handlers is handlers
    assert manager.window._event_stack[-1]["on_key_press"] is handlers[0]
