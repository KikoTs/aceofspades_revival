from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3

class ShotgunWeapon(Weapon):
    name = strings.SHOTGUN
    damage = (A1280, A1281, A1282, A1283, A1283)
    block_damage = A1285
    range = A1268
    shoot_sound = SHOTGUN_SHOOT_SOUND
    reload_sound = 'shotgunreload'
    reload_done_sound = 'cock'
    shoot_interval = A1271
    reload_time = A1269
    accuracy_min = A1272
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1273
    recoil_up = A1278
    recoil_side = A1279
    ammo = (A1289, A1289, A1286, A1287, A1288)
    clip_reload = True
    pellets = A1290
    short_ranged_distance = 25
    model = [SHOTGUN_MODEL]
    view_model = [SHOTGUN_VIEW_MODEL]
    casing = SHOTGUN_CASING
    tracer = SHOTGUN_TRACER
    sight = SHOTGUN_SIGHT
    image = TOOL_IMAGES[SHOTGUN_TOOL]
    accuracy_spread_min = A1274
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1275
    accuracy_spread_increase_per_shot = A1276
    accuracy_spread_reduction_speed = A1277
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SHOTGUN)
    muzzle_flash_scale = 1.0
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SHOTGUN_VIEW)
    muzzle_flash_offset = Vector3(-6.0, 36.0, -3.0)
    muzzle_flash_view_offset = Vector3(-0.05, 0.12, 0.8)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
