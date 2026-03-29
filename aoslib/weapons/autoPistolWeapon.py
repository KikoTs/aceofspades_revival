from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from aoslib import media

class AutoPistolWeapon(Weapon):
    name = strings.AUTOMATIC_PISTOL
    damage = (A1207, A1208, A1209, A1210, A1210)
    block_damage = A1212
    range = A1195
    shoot_sound = BLANK_SOUND
    reload_sound = A2964
    shoot_interval = A1198
    reload_time = A1196
    accuracy_min = A1199
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1200
    recoil_up = A1205
    recoil_side = A1206
    ammo = (A1216, A1216, A1213, A1214, A1215)
    clip_reload = False
    short_ranged_distance = None
    model = [AUTOPISTOL_MODEL]
    view_model = [AUTOPISTOL_VIEW_MODEL]
    casing = AUTOPISTOL_CASING
    tracer = AUTOPISTOL_TRACER
    sight = AUTOPISTOL_SIGHT
    image = TOOL_IMAGES[AUTOMATIC_PISTOL_TOOL]
    sight_pos = (0.0, -0.18, -0.8)
    accuracy_spread_min = A1201
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1202
    accuracy_spread_increase_per_shot = A1203
    accuracy_spread_reduction_speed = A1204
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_AUTOPISTOL)
    muzzle_flash_duration = 0.05
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_AUTOPISTOL_VIEW)
    muzzle_flash_offset = Vector3(-19.0, 71.0, -13.0)
    muzzle_flash_view_offset = Vector3(-0.0, 0.12, 0.5)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    shooting = False
    model_size = 0.04
    view_model_size = 0.035

    def __init__(self, character):
        super(AutoPistolWeapon, self).__init__(character)
        self.looping_fire_sound = None
        self.play_shoot_sound = False
        self.time_firing = 0.0
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.15, -0.05, 0.2)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, 0.05, -0.05)
        return

    def on_unset(self):
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.time_firing = 0.0
        super(AutoPistolWeapon, self).on_unset()
        return

    def update(self, dt):
        if self.character.can_shoot_primary() and self.can_fire():
            if not self.looping_fire_sound:
                self.looping_fire_sound = self.play_sound(A2962, position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.shooting = True
        if self.shooting:
            self.time_firing += dt
        if self.time_firing >= A1198:
            self.play_shoot_sound = False
            self.time_firing -= A1198
            if not self.character.can_shoot_primary() or not self.can_fire():
                self.shooting = False
            if not self.shooting:
                if self.looping_fire_sound:
                    self.looping_fire_sound.close()
                    self.looping_fire_sound = None
                self.play_sound(A2963, position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                self.time_firing = 0.0
        if self.looping_fire_sound:
            pos = self.get_audio_pos()
            if pos:
                self.looping_fire_sound.set_position(*pos)
        return super(AutoPistolWeapon, self).update(dt)
