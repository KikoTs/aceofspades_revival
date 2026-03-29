from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3

class SnubPistolWeapon(Weapon):
    name = strings.SNUB_PISTOL_TOOL
    damage = (SNUB_PISTOL_DAMAGE_TORSO, SNUB_PISTOL_DAMAGE_HEAD, SNUB_PISTOL_DAMAGE_ARMS, SNUB_PISTOL_DAMAGE_LEGS, SNUB_PISTOL_DAMAGE_LEGS)
    block_damage = SNUB_PISTOL_DAMAGE_BLOCK
    range = SNUB_PISTOL_RANGE
    shoot_sound = SNUB_PISTOL_SHOOT_SOUND
    reload_sound = 'snub_reload'
    reload_done_sound = 'snub_cock'
    shoot_interval = SNUB_PISTOL_SHOOT_INTERVAL
    reload_time = SNUB_PISTOL_RELOAD_TIME
    accuracy = SNUB_PISTOL_ACCURACY
    recoil_up = SNUB_PISTOL_RECOIL_UP
    recoil_side = SNUB_PISTOL_RECOIL_SIDE
    ammo = (SNUB_PISTOL_AMMO_CLIP_SIZE, SNUB_PISTOL_AMMO_CLIP_SIZE, SNUB_PISTOL_AMMO_MAX, SNUB_PISTOL_AMMO_INITIAL_STOCK, SNUB_PISTOL_AMMO_RESTOCK_AMOUNT)
    clip_reload = True
    short_ranged_distance = None
    model = [WEAPON_SNUBNOSEPISTOL_MODEL]
    model_size = 1.3 * BODY_PARTS_SIZE * 0.666
    view_model = [WEAPON_SNUBNOSEPISTOL_VIEW_MODEL]
    sight = WEAPON_SNUBNOSEPISTOL_SIGHT
    casing = WEAPON_SNUBNOSEPISTOL_CASING
    tracer = WEAPON_SNUBNOSEPISTOL_TRACER
    image = TOOL_IMAGES[SNUB_PISTOL_TOOL]
    sight_pos = (0, -0.1, -1)
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SNUB_PISTOL)
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SNUB_PISTOL_VIEW)
    muzzle_flash_offset = Vector3(-19.0, 59.0, -13.0)
    muzzle_flash_view_offset = Vector3(0.0, 0.34, 0.5)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.2, 2.5)
    show_crosshair = ALWAYS_CROSSHAIR

    def __init__(self, character):
        super(SnubPistolWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.12, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.12, 0.0)
