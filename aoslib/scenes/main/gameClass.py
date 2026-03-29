from shared.constants import *
import aoslib.config
from aoslib import strings
from shared.constants_gamemode import A2447
from shared.constants_DLC import get_character_dlc_Name

class GameClass(object):

    def __init__(self, manager, id, disabled_tools, speed_multiplier, config=None, enable_fall_on_water_damage=True):
        self.id = id
        self.manager = manager
        self.disabled_tools = [] if disabled_tools is None else disabled_tools
        self.name = strings.get_by_id(CLASS_NAMES[self.id])
        self.has_jetpack = False
        self.loadout = self.build_class_loadout(config)
        self.gun = self.loadout[0]
        self.damage_multiplier = CLASS_DAMAGE_MULTIPLIER[self.id]
        self.accel_multiplier = CLASS_ACCEL_MULTIPLIER[self.id] * speed_multiplier
        self.sprint_multiplier = CLASS_SPRINT_MULTIPLIER[self.id] * speed_multiplier
        self.crouch_sneak_multiplier = CLASS_CROUCH_SNEAK_MULTIPLIER[self.id] * speed_multiplier
        if enable_fall_on_water_damage:
            self.fall_on_water_damage_multiplier = CLASS_FALL_ON_WATER_DAMAGE_MULTIPLIER[self.id]
        else:
            self.fall_on_water_damage_multiplier = 0.0
        self.jump_multiplier = CLASS_JUMP_MULTIPLIER[self.id]
        self.can_sprint_uphill = CLASS_CAN_SPRINT_UPHILL[self.id]
        self.water_friction = CLASS_WATER_FRICTION[self.id]
        self.falling_damage_min_distance = CLASS_FALLING_DAMAGE_MIN_DISTANCE[self.id]
        self.falling_damage_max_distance = CLASS_FALLING_DAMAGE_MAX_DISTANCE[self.id]
        self.falling_damage_max_damage = CLASS_FALLING_DAMAGE_MAX_DAMAGE[self.id]
        self.body_parts = A268[self.id]
        self.prefabs = []
        self.ugc_tools = []
        if self.manager.game_mode == A2447 or PREFAB_TOOL in self.disabled_tools or self.manager.is_in_mafia_mode():
            self.get_prefabs(config, 0)
        else:
            self.get_prefabs(config, 3)
        self.get_ugc_tools(config, 0)
        return

    def get_prefabs(self, config, noof_selected_prefabs):
        class_id = self.id
        if config and not self.manager.game_mode != A2447:
            saved_prefabs = getattr(config, aoslib.config.prefab_name(class_id))
        else:
            saved_prefabs = []
        available_prefabs = []
        for prefab_list_index in CLASS_ITEMS[class_id][CLASS_PREFABS]:
            prefab_list = PREFAB_LISTS[prefab_list_index]
            for prefab in prefab_list:
                available_prefabs.append(prefab)

        self.prefabs = []
        for saved_prefab in saved_prefabs:
            if saved_prefab in available_prefabs:
                self.prefabs.append(saved_prefab)

        prefab_index = 0
        while len(self.prefabs) < noof_selected_prefabs and len(available_prefabs) >= noof_selected_prefabs:
            if available_prefabs[prefab_index] not in self.prefabs:
                self.prefabs.append(available_prefabs[prefab_index])
            prefab_index += 1

    def get_ugc_tools(self, config, noof_selected_tools):
        class_id = self.id
        available_tools = []
        for tool_list_index in CLASS_ITEMS[class_id][CLASS_UGC_TOOLS]:
            tool_list = UGCTOOL_LISTS[tool_list_index]
            for tool in tool_list:
                available_tools.append(tool)

        tool_index = 0
        while len(self.ugc_tools) < noof_selected_tools and len(available_tools) >= noof_selected_tools:
            if available_tools[tool_index] not in self.ugc_tools:
                self.ugc_tools.append(available_tools[tool_index])
            tool_index += 1

    def get_valid_items(self, items, saved_items, noof_selected_items=1):
        valid_items = []
        if len(items):
            valid_item = -1
            for item in items:
                if item in saved_items and item not in self.disabled_tools:
                    valid_items.append(item)
                    if len(valid_items) == noof_selected_items:
                        break

            if len(valid_items) == 0:
                for item in items:
                    if len(valid_items) < noof_selected_items and item not in self.disabled_tools:
                        valid_items.append(item)

        return valid_items

    def set_common_loadout_items(self, loadout, add_flareblock=False):
        class_items = CLASS_ITEMS[self.id]
        for item in class_items[CLASS_COMMON]:
            if item in self.disabled_tools:
                continue
            if item == FLAREBLOCK_TOOL and add_flareblock == False:
                continue
            if item == BLOCK_TOOL:
                loadout.insert(0, item)
                continue
            loadout.append(item)

    def build_class_loadout(self, config):
        class_id = self.id
        if config:
            saved_loadout = getattr(config, aoslib.config.loadout_name(class_id))
        else:
            saved_loadout = []
        loadout = []
        class_items = CLASS_ITEMS[class_id]
        for index in xrange(CLASS_NOOF_SELECTABLE_ITEMS):
            if index == CLASS_PREFABS:
                continue
            items = self.get_valid_items(class_items[index], saved_loadout)
            for valid_item in items:
                loadout.append(valid_item)
                if valid_item == JETPACK_NORMAL:
                    self.has_jetpack = True
                elif valid_item == A370:
                    self.has_parachute = True

        self.set_common_loadout_items(loadout)
        if not self.manager.is_in_mafia_mode():
            if FLAREBLOCK_TOOL not in self.disabled_tools:
                loadout.append(FLAREBLOCK_TOOL)
            if PREFAB_TOOL not in self.disabled_tools:
                loadout.append(PREFAB_TOOL)
        return loadout

    def is_selectable(self):
        selectable = True
        dlcName = get_character_dlc_Name(self.id)
        if dlcName != None:
            if not self.manager.dlc_manager.is_installed_dlc(dlcName):
                selectable = False
        return selectable
