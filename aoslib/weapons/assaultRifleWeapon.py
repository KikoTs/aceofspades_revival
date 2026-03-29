from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from aoslib import media

class AssaultRifleWeapon(Weapon):
    name = strings.ASSAULT_RIFLE
    damage = (A1924, A1925, A1926, A1927, A1927)
    block_damage = A1929
    range = A1912
    shoot_sound = A2938
    reload_sound = A2940
    shoot_interval = A1915
    reload_time = A1913
    accuracy_min = A1916
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1917
    recoil_up = A1922
    recoil_side = A1923
    ammo = (A1933, A1933, A1930, A1931, A1932)
    clip_reload = False
    short_ranged_distance = None
    model = [ASSAULTRIFLE_MODEL]
    view_model = [ASSAULTRIFLE_VIEW_MODEL]
    casing = ASSAULTRIFLE_CASING
    tracer = ASSAULTRIFLE_TRACER
    sight = ASSAULTRIFLE_SIGHT
    image = TOOL_IMAGES[ASSAULT_RIFLE_TOOL]
    sight_pos = (0.0, -0.07, 0.0)
    accuracy_spread_min = A1918
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1919
    accuracy_spread_increase_per_shot = A1920
    accuracy_spread_reduction_speed = A1921
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_ASSAULTRIFLE)
    muzzle_flash_duration = 0.05
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_ASSAULTRIFLE_VIEW)
    muzzle_flash_offset = Vector3(-21.0, 110.0, -13.0)
    muzzle_flash_view_offset = Vector3(-0.0, 0.12, 0.5)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    shooting = False
    model_size = 0.04
    view_model_size = 0.035

    def __init__(self, character):
        super(AssaultRifleWeapon, self).__init__(character)
        self.play_shoot_sound = False
        self.time_firing = 0.0
        self.total_time_firing = 0.0
        self.burst_active = False
        self.burst_shots_fired = 0
        self.burst_timer = 0.0
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.2, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(-0.1, -0.08, -0.1)

    def on_unset(self):
        self.time_firing = 0.0
        self.total_time_firing = 0.0
        super(AssaultRifleWeapon, self).on_unset()

    def use_primary(self):
        if super(AssaultRifleWeapon, self).use_primary():
            if not self.burst_active:
                self.start_burst()
            return True
        return False

    def start_burst(self):
        self.burst_shots_fired = 1
        self.burst_timer = A1935
        self.burst_active = True
        self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)

    def can_swap(self):
        return not self.is_active() and not self.burst_active

    def set_ammo(self, ammo, clip):
        self.burst_active = False
        super(AssaultRifleWeapon, self).set_ammo(ammo, clip)

    def is_reloadable(self):
        if self.burst_active and self.current_ammo > A1934:
            return False
        return super(AssaultRifleWeapon, self).is_reloadable()

    def update(self, dt):
        if self.burst_active:
            self.burst_timer -= dt
            if self.burst_timer <= 0.0:
                if self.use_primary():
                    self.burst_shots_fired += 1
                    self.burst_timer = A1935
                else:
                    self.burst_active = False
            if self.burst_shots_fired == A1934:
                self.burst_active = False
        return super(AssaultRifleWeapon, self).update(dt)
