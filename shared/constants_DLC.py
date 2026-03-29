from constants_shop import *
from constants import *

class constants_DLC(object):
    pass


DLC_TOOLS = {
    DLC_AppName01: [],
    DLC_AppName02: [
        RIOTSTICK_TOOL,
        MACHETE_TOOL,
        MEDPACK_TOOL,
        RIOTSHIELD_TOOL,
        AUTOMATIC_PISTOL_TOOL,
        CHEMICALBOMB_TOOL,
        GRENADE_LAUNCHER_WEAPON_TOOL,
        STICKY_GRENADE_TOOL,
        MINE_LAUNCHER_TOOL,
        ASSAULT_RIFLE_TOOL,
        LIGHT_MACHINE_GUN_TOOL,
        AUTO_SHOTGUN_TOOL,
        BLOCK_SUCKER_TOOL,
    ],
}
DLC_CHARACTERS = {DLC_AppName01: [], DLC_AppName02: [CLASS_SPECIALIST, CLASS_MEDIC]}


def get_tool_dlc_Name(tool_id):
    dlc_AppName = None
    for k, v in DLC_TOOLS.iteritems():
        if tool_id in v:
            dlc_AppName = k
            break

    return dlc_AppName


def get_character_dlc_Name(character_id):
    dlc_AppName = None
    for k, v in DLC_CHARACTERS.iteritems():
        if character_id in v:
            dlc_AppName = k
            break

    return dlc_AppName


def is_tool_selectable(tool_id, dlc_manager):
    selectable = True
    dlcName = get_tool_dlc_Name(tool_id)
    if dlcName != None:
        if not dlc_manager.is_installed_dlc(dlcName):
            selectable = False
    return selectable


def is_character_selectable(character_id, dlc_manager):
    selectable = True
    dlcName = get_character_dlc_Name(character_id)
    if dlcName != None:
        if not dlc_manager.is_installed_dlc(dlcName):
            selectable = False
    return selectable
