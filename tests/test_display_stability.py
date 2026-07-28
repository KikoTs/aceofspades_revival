import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
CONFIG_PATH = PROJECT_ROOT / "aoslib" / "config.py"
GRAPHICS_MANAGER_PATH = PROJECT_ROOT / "aoslib" / "graphicsManager.py"
GRAPHICS_TAB_PATH = (
    PROJECT_ROOT / "aoslib" / "scenes" / "frontend" / "graphicsTab.py"
)


from display_config import (
    DISPLAY_SETTING_NAMES,
    repair_display_config_file,
    sanitize_display_config,
    write_json_file,
)


def load_configuration_class(update_callback=lambda: None):
    tree = ast.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Configuration"
    )
    module = ast.Module(body=[class_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "copy": copy,
        "DEFAULT_CONFIG": {
            "fullscreen": False,
            "resolution": 0,
            "width": 800,
            "height": 600,
            "window_width": 800,
            "window_height": 600,
            "window_location_x": 0,
            "window_location_y": 0,
        },
        "DISPLAY_SETTING_NAMES": DISPLAY_SETTING_NAMES,
        "sanitize_display_config": sanitize_display_config,
        "write_json_file": write_json_file,
        "update_resolutions": update_callback,
    }
    exec(compile(module, str(CONFIG_PATH), "exec"), namespace)
    return namespace["Configuration"]


class FakeWindow:
    def __init__(self, fail_once=False):
        self.setting_fullscreen = False
        self.fail_once = fail_once
        self.calls = []

    def _record(self, name, fullscreen=None, width=None, height=None):
        self.calls.append((name, fullscreen, width, height))
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("simulated native display failure")

    def set_fullscreen(self, fullscreen, width=None, height=None):
        self._record("set_fullscreen", fullscreen, width, height)

    def set_size(self, width=None, height=None):
        self._record("set_size", None, width, height)

    def set_vsync(self, value):
        self.calls.append(("set_vsync", value, None, None))


class FakeMedia:
    def set_main_volume(self, value):
        pass

    def set_music_volume(self, value):
        pass


def make_configuration(window):
    configuration_class = load_configuration_class()
    config = object.__new__(configuration_class)
    config.manager = SimpleNamespace(
        window=window,
        media=FakeMedia(),
        save_window_position=lambda: None,
    )
    config.changed = False
    config.fullscreen = False
    config.resolution = 0
    config.width = 1920
    config.height = 1080
    config.window_width = 800
    config.window_height = 600
    config.window_location_x = 0
    config.window_location_y = 0
    return config


def load_graphics_manager_module():
    spec = importlib.util.spec_from_file_location(
        "client_graphics_manager_for_test",
        GRAPHICS_MANAGER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_custom_resolution_is_preserved():
    repaired, changes = sanitize_display_config(
        {
            "fullscreen": False,
            "resolution": 0,
            "width": 2560,
            "height": 1440,
            "window_width": 2560,
            "window_height": 1369,
            "window_location_x": -1920,
            "window_location_y": 23,
        }
    )

    assert changes == []
    assert repaired["window_width"] == 2560
    assert repaired["window_height"] == 1369
    assert repaired["window_location_x"] == -1920


def test_invalid_display_pairs_are_repaired_together():
    repaired, changes = sanitize_display_config(
        {
            "fullscreen": "not-a-boolean",
            "resolution": -50,
            "width": 0,
            "height": 1440,
            "window_width": 999999,
            "window_height": 720,
        }
    )

    assert repaired["fullscreen"] is False
    assert repaired["resolution"] == 0
    assert (repaired["width"], repaired["height"]) == (800, 600)
    assert (repaired["window_width"], repaired["window_height"]) == (800, 600)
    assert {change[0] for change in changes} >= {
        "fullscreen",
        "resolution",
        "width",
        "height",
        "window_width",
        "window_height",
    }


def test_display_config_file_repair_preserves_unrelated_settings(tmp_path):
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        json.dumps(
            {
                "fullscreen": False,
                "width": 0,
                "height": 0,
                "window_width": 0,
                "window_height": 0,
                "name": "Kiko",
                "mouse_sensitivity": 0.17,
            }
        ),
        encoding="utf-8",
    )

    changes = repair_display_config_file(str(config_path))
    repaired = json.loads(config_path.read_text(encoding="utf-8"))

    assert changes
    assert repaired["name"] == "Kiko"
    assert repaired["mouse_sensitivity"] == 0.17
    assert (repaired["width"], repaired["height"]) == (800, 600)
    assert (repaired["window_width"], repaired["window_height"]) == (800, 600)
    assert not Path(str(config_path) + ".tmp").exists()


def test_windowed_resolution_change_uses_one_native_resize():
    window = FakeWindow()
    config = make_configuration(window)

    changed = config.apply_display_mode(False, 1280, 720, resolution=3)

    assert changed is True
    assert window.calls == [("set_size", None, 1280, 720)]
    assert (config.window_width, config.window_height) == (1280, 720)
    assert config.resolution == 3
    assert window.setting_fullscreen is False


def test_failed_native_resize_rolls_back_config_and_transition_flag():
    window = FakeWindow(fail_once=True)
    config = make_configuration(window)

    changed = config.apply_display_mode(False, 1280, 720, resolution=3)

    assert changed is False
    assert (config.window_width, config.window_height) == (800, 600)
    assert config.resolution == 0
    assert window.calls == [
        ("set_size", None, 1280, 720),
        ("set_size", None, 800, 600),
    ]
    assert window.setting_fullscreen is False


def test_graphics_manager_custom_mode_uses_real_dimensions(monkeypatch):
    graphics = load_graphics_manager_module()
    import sys

    fake_aoslib = SimpleNamespace(strings=SimpleNamespace(CUSTOM="Custom"))
    monkeypatch.setitem(sys.modules, "aoslib", fake_aoslib)
    monkeypatch.setitem(sys.modules, "aoslib.strings", fake_aoslib.strings)
    config = SimpleNamespace(
        fullscreen=False,
        width=1920,
        height=1080,
        window_width=1234,
        window_height=777,
        resolution=0,
        screen_resolutions_by_string={},
        sorted_screen_resolutions_for_gui=[],
    )
    manager = graphics.GraphicsManager()
    manager.screen_modes = [
        SimpleNamespace(width=800, height=600),
        SimpleNamespace(width=1024, height=768),
    ]

    manager.initialise(config)

    custom = config.sorted_screen_resolutions_for_gui[0][1]
    assert (custom.width, custom.height) == (1234, 777)
    assert custom.resolution_string == "Custom"
    assert all(
        (resolution.width, resolution.height) != (0, 0)
        for pair, resolution in config.sorted_screen_resolutions_for_gui
    )
    assert (manager.current_resolution.width, manager.current_resolution.height) == (
        1234,
        777,
    )


def test_graphics_tab_applies_resolution_atomically():
    tree = ast.parse(GRAPHICS_TAB_PATH.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "GraphicsTab"
    )
    method = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_changes"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    ]

    assert sum(node.func.attr == "apply_display_mode" for node in calls) == 1
    dimension_sets = []
    for node in calls:
        if node.func.attr != "set" or not node.args:
            continue
        if isinstance(node.args[0], ast.Constant):
            dimension_sets.append(node.args[0].value)
    assert not {
        "width",
        "height",
        "window_width",
        "window_height",
    }.intersection(dimension_sets)
