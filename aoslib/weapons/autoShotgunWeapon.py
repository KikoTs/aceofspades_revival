from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3

class AutoShotgunWeapon(Weapon):
    name = strings.AUTO_SHOTGUN
    damage = (A1970, A1971, A1972, A1973, A1973)
    block_damage = A1975
    range = A1958
    shoot_sound = A2954
    reload_sound = A2955
    shoot_interval = A1961
    reload_time = A1959
    accuracy_min = A1962
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1963
    recoil_up = A1968
    recoil_side = A1969
    ammo = (A1979, A1979, A1976, A1977, A1978)
    clip_reload = False
    pellets = A1980
    short_ranged_distance = 25
    model = [AUTOSHOTGUN_MODEL]
    view_model = [AUTOSHOTGUN_VIEW_MODEL]
    casing = AUTOSHOTGUN_CASING
    tracer = AUTOSHOTGUN_TRACER
    sight = AUTOSHOTGUN_SIGHT
    image = TOOL_IMAGES[AUTO_SHOTGUN_TOOL]
    accuracy_spread_min = A1964
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1965
    accuracy_spread_increase_per_shot = A1966
    accuracy_spread_reduction_speed = A1967
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SHOTGUN)
    muzzle_flash_scale = 0.6
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SHOTGUN_VIEW)
    muzzle_flash_offset = Vector3(-14.0, 72.0, -5.8)
    muzzle_flash_view_offset = Vector3(-0.05, 0.12, 0.8)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    model_size = 0.05
    view_model_size = 0.05

    def __init__(self, character):
        super(AutoShotgunWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.125, 0.13)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.1, -0.2)

    def update_ammo(self):
        super(AutoShotgunWeapon, self).update_ammo()
        ammo, clip = self.get_ammo()
