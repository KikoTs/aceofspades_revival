from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3

class PistolWeapon(Weapon):
    name = strings.PISTOL
    damage = (PISTOL_DAMAGE_TORSO, PISTOL_DAMAGE_HEAD, PISTOL_DAMAGE_ARMS, PISTOL_DAMAGE_LEGS, PISTOL_DAMAGE_LEGS)
    block_damage = PISTOL_DAMAGE_BLOCK
    range = PISTOL_RANGE
    shoot_sound = PISTOL_SHOOT_SOUND
    reload_sound = 'pistolreload'
    shoot_interval = PISTOL_SHOOT_INTERVAL
    reload_time = PISTOL_RELOAD_TIME
    accuracy = PISTOL_ACCURACY
    recoil_up = PISTOL_RECOIL_UP
    recoil_side = PISTOL_RECOIL_SIDE
    ammo = (PISTOL_AMMO_CLIP_SIZE, PISTOL_AMMO_CLIP_SIZE, PISTOL_AMMO_MAX, PISTOL_AMMO_INITIAL_STOCK, PISTOL_AMMO_RESTOCK_AMOUNT)
    clip_reload = False
    short_ranged_distance = None
    model = [PISTOL_MODEL]
    view_model = [PISTOL_VIEW_MODEL]
    sight = PISTOL_SIGHT
    casing = PISTOL_CASING
    tracer = PISTOL_TRACER
    image = TOOL_IMAGES[PISTOL_TOOL]
    sight_pos = (0, -0.1, -1)
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_PISTOL)
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_PISTOL_VIEW)
    muzzle_flash_offset = Vector3(-13.0, 53.0, -6.0)
    muzzle_flash_view_offset = Vector3(-0.05, 0.12, 0.35)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 1.5)
    show_crosshair = ALWAYS_CROSSHAIR
