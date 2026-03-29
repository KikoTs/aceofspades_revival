import json, aosKeys as key, copy
from shared.steam import SteamGetPersonaName
from shared import constants
from shared.constants import REGION_US_WEST, REGION_US_EAST, REGION_EUROPE, REGION_AUSTRALIA
from aoslib import update_resolutions
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
        self.set_dict(self.old_config, from_restore=True)
        self.changed = False

    def save(self, set_old_config=True):
        if set_old_config:
            self.old_config = self.get_dict()
        data = self.get_dict()
        self.changed = False
        try:
            with open(self.filename, 'wb') as f:
                json.dump(data, f, indent=4)
        except IOError:
            pass

    def set(self, name, value, from_restore=False):
        self.changed = True
        setattr(self, name, value)
        if self.manager:
            if name == 'fullscreen':
                self.manager.window.setting_fullscreen = True
                if self.fullscreen:
                    self.manager.save_window_position()
                    self.manager.window.set_fullscreen(True, width=self.width, height=self.height)
                else:
                    self.manager.window.set_fullscreen(False, width=self.window_width, height=self.window_height)
                if not from_restore:
                    update_resolutions()
            elif name == 'vsync':
                self.manager.window.set_vsync(self.vsync)
            elif name == 'master_volume':
                self.manager.media.set_main_volume(self.master_volume)
            elif name == 'music_volume':
                self.manager.media.set_music_volume(self.music_volume)
            elif name == 'width':
                if self.fullscreen:
                    self.manager.window.setting_fullscreen = True
                    self.manager.window.set_fullscreen(True, width=self.width, height=self.height)
                if not from_restore:
                    update_resolutions()
            elif name == 'window_width' or name == 'window_height':
                if not self.fullscreen:
                    self.manager.window.set_size(width=self.window_width, height=self.window_height)
                if not from_restore:
                    update_resolutions()
        return True
