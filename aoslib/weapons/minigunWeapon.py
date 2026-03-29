from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from shared.common import clamp
from aoslib.animations.animWeaponShoot import *
from aoslib.animations.animRoll import *
from aoslib import strings
from aoslib import media

class MinigunWeapon(Weapon):
    name = strings.MINIGUN
    damage = (A1258, A1259, A1260, A1261, A1261)
    block_damage = A1263
    range = A1239
    shoot_sound = 'minigun_fire_single'
    reload_sound = 'minigunreload'
    shoot_interval_initial = A1242
    shoot_interval_cap = shoot_interval_initial + A1245
    shoot_interval = shoot_interval_initial
    shoot_interval_active_alteration_per_second = A1243
    shoot_interval_inactive_alteration_per_second = A1244
    reload_time = A1240
    accuracy_min = A1250
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1251
    recoil_up = A1256
    recoil_side = A1257
    ammo = (A1267, A1267, A1264, A1265, A1266)
    clip_reload = False
    short_ranged_distance = None
    model = [MINIGUN_BODY_MODEL, MINIGUN_BARREL_MODEL]
    view_model = [
     MINIGUN_BODY_VIEW_MODEL, MINIGUN_BARREL_VIEW_MODEL]
    casing = MINIGUN_CASING
    tracer = MINIGUN_TRACER
    sight = MINIGUN_SIGHT
    image = TOOL_IMAGES[MINIGUN_TOOL]
    sight_pos = (0.0, -0.2, 0.0)
    accuracy_spread_min = A1252
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1253
    accuracy_spread_increase_per_shot = A1254
    accuracy_spread_reduction_speed = A1255
    can_zoom = False
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    spin_speed = 0.0
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_MINIGUN)
    muzzle_flash_scale = 0.75
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_MINIGUN_VIEW)
    muzzle_flash_offset = Vector3(-9.5, 58.0, 5.0)
    muzzle_flash_view_offset = Vector3(0.0, 0.12 - 0.30000000000000004, 2.0)
    time_loop_firing = 0.0
    is_loop_shooting = False

    def __init__(self, character):
        super(MinigunWeapon, self).__init__(character)
        self.initial_position[1] = Vector3(0.0, -0.30000000000000004, 1.1)
        self.reset_position(1)
        self.animations['barrel_roll'] = AnimRoll(speed=self.spin_speed)
        self.spin_sound = None
        self.looping_fire_sound = None
        self.time_loop_firing = 0.0
        self.is_loop_shooting = False
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MINIGUN)
        return

    def can_shoot_primary(self):
        if self.spin_speed > A1248:
            return super(MinigunWeapon, self).can_shoot_primary()
        else:
            return False

    def on_unset(self):
        if self.spin_sound:
            self.spin_sound.close()
            self.spin_sound = None
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.play_shoot_sound = True
        self.time_loop_firing = 0.0
        self.is_loop_shooting = False
        self.spin_speed = 0.0
        self.shoot_interval = self.shoot_interval_initial
        super(MinigunWeapon, self).on_unset()
        return

    def update(self, dt):
        if self.spin_speed > 0:
            if not self.spin_sound:
                self.spin_sound = self.play_sound('minigun_loop', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
        elif self.spin_sound:
            self.spin_sound.close()
            self.spin_sound = None
        if self.spin_sound:
            pos = self.get_audio_pos()
            if pos:
                self.spin_sound.set_position(*pos)
            self.spin_sound.set_pitch(self.spin_speed / float(A1247))
            spin_factor = clamp(self.spin_speed / float(A1247))
            volume = (spin_factor - A1249) / (1.0 - A1249)
            volume = clamp(volume)
            self.spin_sound.set_volume(volume)
        if self.spin_speed >= A1247 and self.character.can_shoot_primary() and self.can_fire():
            self.play_shoot_sound = False
            if not self.looping_fire_sound:
                self.looping_fire_sound = self.play_sound('minigun_fire_loop', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.is_loop_shooting = True
        if self.looping_fire_sound:
            self.time_loop_firing += dt
        if self.time_loop_firing >= A1246:
            self.play_shoot_sound = False
            self.time_loop_firing -= A1246
            if not self.character.can_shoot_primary() or not self.can_fire():
                self.is_loop_shooting = False
            if not self.is_loop_shooting:
                if self.looping_fire_sound:
                    self.looping_fire_sound.close()
                    self.looping_fire_sound = None
                self.play_sound('minigun_fire_tail', position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                self.time_loop_firing = 0.0
                self.play_shoot_sound = True
        if self.looping_fire_sound:
            pos = self.get_audio_pos()
            if pos:
                self.looping_fire_sound.set_position(*pos)
        if (self.character.can_shoot_primary() or self.character.can_shoot_secondary()) and not self.character.reloading:
            self.shoot_interval = clamp(self.shoot_interval + self.shoot_interval_active_alteration_per_second * dt, min(self.shoot_interval_initial, self.shoot_interval_cap), max(self.shoot_interval_initial, self.shoot_interval_cap))
        else:
            self.shoot_interval = clamp(self.shoot_interval + self.shoot_interval_inactive_alteration_per_second * dt, min(self.shoot_interval_initial, self.shoot_interval_cap), max(self.shoot_interval_initial, self.shoot_interval_cap))
        self.spin_speed = 1 * (A1247 * abs((self.shoot_interval - self.shoot_interval_initial) / (self.shoot_interval_cap - self.shoot_interval_initial)))
        if self.spin_speed > 0:
            if not self.animations['barrel_roll'].is_playing():
                self.animations['barrel_roll'].start()
            self.animations['barrel_roll'].set_speed(self.spin_speed)
        elif self.animations['barrel_roll'].is_playing():
            self.animations['barrel_roll'].stop()
        return super(MinigunWeapon, self).update(dt)

    def apply_animations(self, model_index):
        self.animation_position_offset[model_index] = Vector3(0.0, 0.0, 0.0)
        self.animation_orientation_offset[model_index] = Vector3(0.0, 0.0, 0.0)
        animation = self.animations['weapon_shoot']
        if animation.is_playing():
            self.animation_position_offset[model_index] += animation.get_position()
            self.animation_orientation_offset[model_index] += animation.get_orientation()
        if model_index == 1:
            animation = self.animations['barrel_roll']
            self.animation_orientation_offset[model_index] += animation.get_orientation()
