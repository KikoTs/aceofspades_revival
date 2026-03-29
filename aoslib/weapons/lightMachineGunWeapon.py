from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from aoslib import media

class LightMachineGunWeapon(Weapon):
    name = strings.LIGHT_MACHINE_GUN
    damage = (A1948, A1949, A1950, A1951, A1951)
    block_damage = A1953
    range = A1936
    shoot_sound = BLANK_SOUND
    reload_sound = A2949
    shoot_interval = A1939
    reload_time = A1937
    accuracy_min = A1940
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1941
    recoil_up = A1946
    recoil_side = A1947
    ammo = (A1957, A1957, A1954, A1955, A1956)
    clip_reload = False
    short_ranged_distance = None
    model = [LIGHTMACHINEGUN_MODEL]
    view_model = [LIGHTMACHINEGUN_VIEW_MODEL]
    casing = LIGHTMACHINEGUN_CASING
    tracer = LIGHTMACHINEGUN_TRACER
    sight = LIGHTMACHINEGUN_SIGHT
    image = TOOL_IMAGES[LIGHT_MACHINE_GUN_TOOL]
    sight_pos = (0.0, -0.1, 0.0)
    accuracy_spread_min = A1942
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1943
    accuracy_spread_increase_per_shot = A1944
    accuracy_spread_reduction_speed = A1945
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_LIGHTMACHINEGUN)
    muzzle_flash_duration = 0.05
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_LIGHTMACHINEGUN_VIEW)
    muzzle_flash_offset = Vector3(-13.0, 91.0, -8.5)
    muzzle_flash_view_offset = Vector3(-0.0, 0.12, 0.5)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    shooting = False
    model_size = 0.055
    view_model_size = 0.055

    def __init__(self, character):
        super(LightMachineGunWeapon, self).__init__(character)
        self.looping_fire_sound = None
        self.play_shoot_sound = False
        self.time_firing = 0.0
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.0, 0.25)
                self.reset_position(model_index)

        return

    def on_unset(self):
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.time_firing = 0.0
        super(LightMachineGunWeapon, self).on_unset()
        return

    def update(self, dt):
        if self.character.can_shoot_primary() and self.can_fire():
            if not self.looping_fire_sound:
                self.looping_fire_sound = self.play_sound(A2947, position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.shooting = True
        if self.shooting:
            self.time_firing += dt
        if self.time_firing >= A1939:
            self.play_shoot_sound = False
            self.time_firing -= A1939
            if not self.character.can_shoot_primary() or not self.can_fire():
                self.shooting = False
            if not self.shooting:
                if self.looping_fire_sound:
                    self.looping_fire_sound.close()
                    self.looping_fire_sound = None
                self.play_sound(A2948, position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                self.time_firing = 0.0
        if self.looping_fire_sound:
            pos = self.get_audio_pos()
            if pos:
                self.looping_fire_sound.set_position(*pos)
        return super(LightMachineGunWeapon, self).update(dt)
