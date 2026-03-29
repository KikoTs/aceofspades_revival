from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings

class ClassicRifleWeapon(Weapon):
    name = strings.RIFLE
    damage = (RIFLE_DAMAGE_TORSO, RIFLE_DAMAGE_HEAD, RIFLE_DAMAGE_ARMS, RIFLE_DAMAGE_LEGS, RIFLE_DAMAGE_LEGS)
    block_damage = RIFLE_DAMAGE_BLOCK
    range = RIFLE_RANGE
    shoot_sound = SEMI_SHOOT_SOUND
    reload_sound = 'classic_semi_reload'
    shoot_interval = RIFLE_SHOOT_INTERVAL
    reload_time = RIFLE_RELOAD_TIME
    accuracy = RIFLE_ACCURACY
    recoil_up = RIFLE_RECOIL_UP
    recoil_side = RIFLE_RECOIL_SIDE
    ammo = (RIFLE_AMMO_CLIP_SIZE, RIFLE_AMMO_CLIP_SIZE, RIFLE_AMMO_MAX, RIFLE_AMMO_INITIAL_STOCK, RIFLE_AMMO_RESTOCK_AMOUNT)
    clip_reload = False
    short_ranged_distance = None
    show_crosshair = UNZOOMED_CROSSHAIR
    model = [SEMI_MODEL]
    view_model = [SEMI_VIEW_MODEL]
    casing = SEMI_CASING
    tracer = SEMI_TRACER
    sight = SEMI_SIGHT
    pin = SEMI_PIN
    image = TOOL_IMAGES[RIFLE_TOOL]
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_RIFLE)
