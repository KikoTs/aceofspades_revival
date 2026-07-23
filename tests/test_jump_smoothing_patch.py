import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


MODULE_PATH = Path(__file__).resolve().parents[1] / "aoslib" / "jump_smoothing_patch.py"


class FakeWorldObject:
    def __init__(self):
        self.position = [10.0, 20.0, 30.0]
        self.airborne = False
        self.jump = True
        self.jump_this_frame = False
        self.velocity = [0.0, 0.0, 0.0]

    def set_position(self, x, y, z):
        self.position[:] = [float(x), float(y), float(z)]


def load_patch(character_class):
    character_module = ModuleType("aoslib.character")
    character_module.Character = character_class
    sys.modules["aoslib.character"] = character_module
    spec = importlib.util.spec_from_file_location("client_jump_smoothing_patch", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_character(
    *, corrected_position, airborne, initial_velocity=(0.0, 0.0, 0.0)
):
    class FakeCharacter:
        def __init__(self):
            self.world_object = FakeWorldObject()
            self.world_object.velocity[:] = list(initial_velocity)

        def update(self, *args, **kwargs):
            self.last_update_call = (args, kwargs)
            self.world_object.set_position(*corrected_position)
            self.world_object.jump_this_frame = True
            self.world_object.airborne = airborne
            self.world_object.velocity[2] = -0.408525 if airborne else 0.0
            return "native-result"

    return FakeCharacter


def test_large_restore_is_suppressed_for_an_accepted_jump():
    character_class = make_character(
        corrected_position=(8.0, 20.0, 30.0),
        airborne=True,
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    assert character.update() == "native-result"
    assert character.world_object.position == [10.0, 20.0, 30.0]


def test_large_backward_rejected_restore_keeps_native_vertical_correction():
    character_class = make_character(
        corrected_position=(8.0, 19.0, 31.0),
        airborne=False,
        initial_velocity=(0.5, 0.0, 0.0),
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    character.update()
    assert character.world_object.position == [10.0, 20.0, 31.0]


def test_large_forward_rejected_step_correction_remains_native():
    character_class = make_character(
        corrected_position=(12.0, 20.0, 31.0),
        airborne=False,
        initial_velocity=(0.5, 0.0, 0.0),
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    character.update()
    assert character.world_object.position == [12.0, 20.0, 31.0]


def test_small_rejected_step_correction_remains_native():
    character_class = make_character(
        corrected_position=(9.9, 20.0, 30.0),
        airborne=False,
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    character.update()
    assert character.world_object.position == [9.9, 20.0, 30.0]


def test_small_accepted_jump_restore_remains_native():
    character_class = make_character(
        corrected_position=(9.9, 20.0, 30.0),
        airborne=True,
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    character.update()
    assert character.world_object.position == [9.9, 20.0, 30.0]


def test_native_update_arguments_are_forwarded_unchanged():
    character_class = make_character(
        corrected_position=(9.9, 20.0, 30.0),
        airborne=True,
    )
    patch = load_patch(character_class)

    assert patch.install() is True
    character = character_class()
    character.update(1.0 / 60.0, ["collision"])
    assert character.last_update_call == ((1.0 / 60.0, ["collision"]), {})


def test_disable_environment_leaves_character_untouched():
    character_class = make_character(
        corrected_position=(8.0, 20.0, 30.0),
        airborne=True,
    )
    original_update = character_class.update
    patch = load_patch(character_class)
    previous = os.environ.get("AOS_DISABLE_CHARACTER_JUMP_SMOOTHING")
    os.environ["AOS_DISABLE_CHARACTER_JUMP_SMOOTHING"] = "1"
    try:
        assert patch.install() is False
        assert character_class.update is original_update
    finally:
        if previous is None:
            del os.environ["AOS_DISABLE_CHARACTER_JUMP_SMOOTHING"]
        else:
            os.environ["AOS_DISABLE_CHARACTER_JUMP_SMOOTHING"] = previous
