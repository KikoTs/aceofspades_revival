from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3

class Shotgun2Weapon(Weapon):
    name = strings.SHOTGUN2
    damage = (A1326, A1327, A1328, A1329, A1329)
    block_damage = A1331
    range = A1314
    first_barrel_sound = SHOTGUN2_SHOOT_SOUND
    second_barrel_sound = SHOTGUN2_SECOND_SHOOT_SOUND
    shoot_sound = first_barrel_sound
    reload_sound = 'shotgunreload'
    reload_done_sound = 'cock'
    shoot_interval = A1317
    reload_time = A1315
    accuracy_min = A1318
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1319
    recoil_up = A1324
    recoil_side = A1325
    ammo = (A1335, A1335, A1332, A1333, A1334)
    clip_reload = True
    pellets = A1336
    short_ranged_distance = 25
    model = [SHOTGUN2_MODEL]
    view_model = [SHOTGUN2_VIEW_MODEL]
    casing = SHOTGUN2_CASING
    tracer = SHOTGUN2_TRACER
    sight = SHOTGUN2_SIGHT
    image = TOOL_IMAGES[SHOTGUN2_TOOL]
    accuracy_spread_min = A1320
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1321
    accuracy_spread_increase_per_shot = A1322
    accuracy_spread_reduction_speed = A1323
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SHOTGUN)
    muzzle_flash_scale = 1.0
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SHOTGUN_VIEW)
    muzzle_flash_offset = Vector3(-6.0, 36.0, -3.0)
    muzzle_flash_view_offset = Vector3(-0.05, 0.12, 0.8)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)

    def __init__(self, character):
        super(Shotgun2Weapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.1, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.1, -0.0)

    def update_ammo(self):
        super(Shotgun2Weapon, self).update_ammo()
        ammo, clip = self.get_ammo()
        if ammo > 1:
            self.shoot_sound = self.first_barrel_sound
        else:
            self.shoot_sound = self.second_barrel_sound
