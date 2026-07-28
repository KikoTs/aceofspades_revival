import json, aosKeys as key, copy
from shared.steam import SteamGetPersonaName
from shared import constants
from shared.constants import REGION_US_WEST, REGION_US_EAST, REGION_EUROPE, REGION_AUSTRALIA
from aoslib import update_resolutions
from display_config import (
    DISPLAY_SETTING_NAMES,
    sanitize_display_config,
    write_json_file,
)
A2265 = True
MAIN_DEFAULT = {'master_volume': 1.0, 
   'music_volume': 1.0, 
   'fullscreen': True, 
   'invert_mouse': 0}
GRAPHICS_DEFAULT = {'gfx_quality': 0, 
   'resolution': 0, 
   'antialias': 0, 
   'texture_quality': 1, 
   'detail_level': 1, 
   'effect_quality': 1, 
   'draw_distance': 192, 
   'model_detail': 2, 
   'vsync': False, 
   'width': 800, 
   'height': 600, 
   'window_location_x': 0, 
   'window_location_y': 0, 
   'window_width': 800, 
   'window_height': 600}
CONTROL_DEFAULT = {'forward': (key.W), 
   'backward': (key.S), 
   'left': (key.A), 
   'right': (key.D), 
   'jump': (key.SPACE), 
   'crouch': (key.LCTRL), 
   'sneak': (key.V), 
   'sprint': (key.LSHIFT), 
   'mouse_sensitivity': 0.1, 
   'reload': (key.R), 
   'global_chat': (key.T), 
   'team_chat': (key.Y), 
   'show_map': (key.M), 
   'weapon_custom': (key.E), 
   'use_command2': 0, 
   'map_vote_1': (key.F1), 
   'map_vote_2': (key.F2), 
   'map_vote_3': (key.F3), 
   'camera_pan': (key.P), 
   'voice_record': (key.B), 
   'view_scores': (key.TAB), 
   'change_team': (key.PERIOD), 
   'change_class': (key.COMMA), 
   'kick_player': (key.K), 
   'server_region': REGION_US_WEST, 
   'palette_left': (key.LEFT), 
   'palette_right': (key.RIGHT), 
   'palette_up': (key.UP), 
   'palette_down': (key.DOWN), 
   'toggle_hud': None, 
   'screenshot': (key.F11), 
   'aim': None, 
   'menu': (key.ESCAPE), 
   'cancel_prefab_placement': (key.Q), 
   'carve_prefab': (key.C), 
   'quick_save': (key.F10), 
   'tool_help': (key.H), 
   'ugc_settings': (key.X), 
   'hover': (key.Z)}
DEFAULTS = {'Main': MAIN_DEFAULT, 
   'Graphics': GRAPHICS_DEFAULT, 
   'Controls': CONTROL_DEFAULT}
SPECTATOR_DEFAULT = {'draw_names': True}
DEFAULT_CONFIG = {}

def loadout_name(class_id):
    return 'loadout' + str(class_id)


def prefab_name(class_id):
    return 'prefabs' + str(class_id)


for class_id in range(constants.CLASS_NOOF):
    DEFAULT_CONFIG[loadout_name(class_id)] = []
    DEFAULT_CONFIG[prefab_name(class_id)] = []

DEFAULT_CONFIG.update(MAIN_DEFAULT)
DEFAULT_CONFIG.update(GRAPHICS_DEFAULT)
DEFAULT_CONFIG.update(CONTROL_DEFAULT)
DEFAULT_CONFIG.update(SPECTATOR_DEFAULT)

class Configuration(object):
    manager = None
    changed = False
    sorted_screen_resolutions_for_gui = None
    screen_resolutions_by_string = {}

    def __init__(self, filename, reset=False):
        self.filename = filename
        data = {}
        if not reset:
            try:
                with open(filename, 'rb') as f:
                    data = json.load(f)
            except IOError:
                pass

        self.set_dict(data)
        self.old_config = data
        self.changed = False
        name = SteamGetPersonaName()
        if name != None:
            self.set('name', name)
            self.set('debug', False)
        else:
            self.set('name', 'Deuce')
            self.set('debug', False)
        return

    def set_defaults(self, name):
        defaults = DEFAULTS.get(name)
        if defaults:
            for name, value in defaults.iteritems():
                self.set(name, value)

    def set_dict(self, data, from_restore=False):
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        cfg.update(data)
        cfg, ignored_changes = sanitize_display_config(cfg)
        for name, value in cfg.iteritems():
            self.set(name, value, from_restore)

        if not from_restore:
            self.orig_detail_level = self.detail_level

    def get_dict(self):
        data = {}
        for name in DEFAULT_CONFIG:
            data[name] = getattr(self, name)

        return data

    def restore(self):
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        cfg.update(self.old_config)
        cfg, ignored_changes = sanitize_display_config(cfg)
        display_settings = {}
        for name in DISPLAY_SETTING_NAMES:
            display_settings[name] = cfg.pop(name)
        for name, value in cfg.iteritems():
            self.set(name, value, from_restore=True)
        restored = self._apply_display_settings(
            display_settings,
            from_restore=True,
        )
        self.changed = False
        try:
            update_resolutions()
        except Exception:
            pass
        return restored

    def save(self, set_old_config=True):
        data = self.get_dict()
        try:
            write_json_file(self.filename, data)
        except (IOError, OSError, TypeError, ValueError):
            return False
        if set_old_config:
            self.old_config = copy.deepcopy(data)
        self.changed = False
        return True

    def _display_settings(self):
        settings = {}
        for name in DISPLAY_SETTING_NAMES:
            settings[name] = getattr(self, name)
        return settings

    def _apply_display_settings(self, settings, from_restore=False):
        previous = self._display_settings()
        target = previous.copy()
        target.update(settings)
        target, ignored_changes = sanitize_display_config(target)
        for name in DISPLAY_SETTING_NAMES:
            setattr(self, name, target[name])
        self.changed = True

        if not self.manager:
            return True

        previous_width = (
            previous['width']
            if previous['fullscreen']
            else previous['window_width']
        )
        previous_height = (
            previous['height']
            if previous['fullscreen']
            else previous['window_height']
        )
        target_width = (
            target['width']
            if target['fullscreen']
            else target['window_width']
        )
        target_height = (
            target['height']
            if target['fullscreen']
            else target['window_height']
        )
        needs_transition = (
            previous['fullscreen'] != target['fullscreen']
            or previous_width != target_width
            or previous_height != target_height
        )
        window = self.manager.window
        try:
            if needs_transition:
                window.setting_fullscreen = True
                if target['fullscreen']:
                    if not previous['fullscreen']:
                        try:
                            self.manager.save_window_position()
                        except Exception:
                            pass
                    window.set_fullscreen(
                        True,
                        width=target_width,
                        height=target_height,
                    )
                elif previous['fullscreen']:
                    window.set_fullscreen(
                        False,
                        width=target_width,
                        height=target_height,
                    )
                else:
                    window.set_size(
                        width=target_width,
                        height=target_height,
                    )
        except Exception:
            for name in DISPLAY_SETTING_NAMES:
                setattr(self, name, previous[name])
            try:
                if previous['fullscreen']:
                    window.set_fullscreen(
                        True,
                        width=previous_width,
                        height=previous_height,
                    )
                elif target['fullscreen']:
                    window.set_fullscreen(
                        False,
                        width=previous_width,
                        height=previous_height,
                    )
                else:
                    window.set_size(
                        width=previous_width,
                        height=previous_height,
                    )
            except Exception:
                pass
            return False
        finally:
            window.setting_fullscreen = False

        if not from_restore:
            try:
                update_resolutions()
            except Exception:
                pass
        return True

    def apply_display_mode(
        self,
        fullscreen,
        width,
        height,
        resolution=None,
        from_restore=False,
    ):
        settings = self._display_settings()
        settings['fullscreen'] = bool(fullscreen)
        if settings['fullscreen']:
            settings['width'] = width
            settings['height'] = height
        else:
            settings['window_width'] = width
            settings['window_height'] = height
        if resolution is not None:
            settings['resolution'] = resolution
        return self._apply_display_settings(settings, from_restore)

    def set(self, name, value, from_restore=False):
        if self.manager and name == 'fullscreen':
            if value:
                width = self.width
                height = self.height
            else:
                width = self.window_width
                height = self.window_height
            return self.apply_display_mode(
                value,
                width,
                height,
                from_restore=from_restore,
            )
        if self.manager and name in (
            'width',
            'height',
            'window_width',
            'window_height',
        ):
            settings = self._display_settings()
            settings[name] = value
            active = (
                self.fullscreen and name in ('width', 'height')
                or not self.fullscreen
                and name in ('window_width', 'window_height')
            )
            if active:
                return self._apply_display_settings(settings, from_restore)
        self.changed = True
        setattr(self, name, value)
        if self.manager:
            if name == 'vsync':
                self.manager.window.set_vsync(self.vsync)
            elif name == 'master_volume':
                self.manager.media.set_main_volume(self.master_volume)
            elif name == 'music_volume':
                self.manager.media.set_music_volume(self.music_volume)
        return True
