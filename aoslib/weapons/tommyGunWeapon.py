from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from aoslib import media

class TommyGunWeapon(Weapon):
    name = strings.TOMMYGUN_TOOL
    damage = (A1229, A1230, A1231, A1232, A1232)
    block_damage = A1234
    range = A1217
    shoot_sound = BLANK_SOUND
    reload_sound = 'tommygun_reload'
    shoot_interval = A1220
    reload_time = A1218
    accuracy_min = A1221
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1222
    recoil_up = A1227
    recoil_side = A1228
    ammo = (A1238, A1238, A1235, A1236, A1237)
    clip_reload = False
    short_ranged_distance = None
    model = [WEAPON_TOMMYGUN_MODEL]
    model_size = 1.3 * BODY_PARTS_SIZE * 0.666
    view_model = [WEAPON_TOMMYGUN_VIEW_MODEL]
    casing = WEAPON_TOMMYGUN_CASING
    tracer = WEAPON_TOMMYGUN_TRACER
    sight = WEAPON_TOMMYGUN_SIGHT
    ring = SMG_RING
    image = TOOL_IMAGES[TOMMYGUN_TOOL]
    sight_pos = (0.0, -0.2, 0.0)
    accuracy_spread_min = A1223
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1224
    accuracy_spread_increase_per_shot = A1225
    accuracy_spread_reduction_speed = A1226
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_TOMMYGUN)
    muzzle_flash_duration = 0.01
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_TOMMYGUN_VIEW)
    muzzle_flash_offset = Vector3(-19.0, 92.0, -14.0)
    muzzle_flash_view_offset = Vector3(-0.0, 0.35, 1.2)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    shooting = False

    def __init__(self, character):
        super(TommyGunWeapon, self).__init__(character)
        self.looping_fire_sound = None
        self.play_shoot_sound = False
        self.time_firing = 0.0
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.12, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.12, 0.0)
        return

    def on_unset(self):
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.time_firing = 0.0
        super(TommyGunWeapon, self).on_unset()
        return

    def update(self, dt):
        if self.character.can_shoot_primary() and self.can_fire():
            if not self.looping_fire_sound:
                self.looping_fire_sound = self.play_sound('tommygun_fire_loop', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.shooting = True
        if self.shooting:
            self.time_firing += dt
        if self.time_firing >= A1220:
            self.play_shoot_sound = False
            self.time_firing -= A1220
            if not self.character.can_shoot_primary() or not self.can_fire():
                self.shooting = False
            if not self.shooting:
                if self.looping_fire_sound:
                    self.looping_fire_sound.close()
                    self.looping_fire_sound = None
                self.play_sound('tommygun_fire_tail', position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                self.time_firing = 0.0
        if self.looping_fire_sound:
            pos = self.get_audio_pos()
            if pos:
                self.looping_fire_sound.set_position(*pos)
        return super(TommyGunWeapon, self).update(dt)
