from tool import Tool
from . import shoot_bullet
from aoslib import media
from aoslib.shaders import PASSTHROUGH_SHADER
import random, math
from shared.glm import Vector3, Matrix4
from aoslib.animations.animWeaponShoot import *
from pyglet.gl import *
from shared.constants import *

class Weapon(Tool):
    damage = None
    range = WEAPON_RANGE
    block_damage = 1
    block_penetration = 2.5
    shoot_sound = None
    reload_sound = None
    shoot_interval = None
    reload_time = None
    reload_done_sound = None
    accuracy = None
    accuracy_zoom = None
    recoil_up = None
    recoil_side = None
    ammo = None
    pellets = 1
    clip_reload = None
    short_ranged_distance = None
    pitch = 0.5
    has_secondary = False
    current_ammo = 0
    current_clip = 0
    pin_scale = 0.02
    sight_pos = (0, 0, 0)
    pin = None
    accuracy_spread_min = 1
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min
    accuracy_spread_increase_per_shot = 1
    accuracy_spread_reduction_speed = 1
    variable_accuracy = False
    muzzle_flash_timer = 0.0
    muzzle_flash_display = None
    muzzle_flash_view_display = None
    muzzle_flash_offset = Vector3(0.0, 0.0, 0.0)
    muzzle_flash_view_offset = Vector3(0.0, 0.0, 0.0)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, 0.0, 0.0)
    muzzle_flash_duration = 0.05
    muzzle_flash_scale = 0.5
    muzzle_flash_rotation = 0.0
    play_shoot_animation = True

    def __init__(self, character):
        self.reload_sound_player = None
        super(Weapon, self).__init__(character)
        if self.play_shoot_animation:
            self.animations['weapon_shoot'] = AnimWeaponShoot(self.shoot_interval)
        return

    def on_unset(self):
        if self.reload_sound_player and self.reload_sound_player.is_playing():
            self.reload_sound_player.close()
        self.accuracy_spread = self.accuracy_spread_min
        super(Weapon, self).on_unset()

    def update(self, dt):
        if self.variable_accuracy:
            self.accuracy_spread = max(self.accuracy_spread - dt * self.accuracy_spread_reduction_speed, self.accuracy_spread_min)
        if self.muzzle_flash_display and self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= dt
        super(Weapon, self).update(dt)

    def restock(self, type=None):
        max_ammo, initial_ammo, max_clip, initial_stock, restock_amount = self.ammo
        if type == AMMO_CRATE:
            if max_clip == 0 or max_clip == None:
                self.current_ammo = min(self.current_ammo + restock_amount, max_ammo)
            else:
                self.current_clip = min(self.current_clip + restock_amount, max_clip)
        else:
            self.current_ammo, self.current_clip = initial_ammo, initial_stock
        self.update_ammo()
        if type == AMMO_CRATE and self.character.main and self.character.weapon_object is self and self.is_reloadable() and self.current_ammo == 0:
            self.character.reload_next_update = True
        return

    def set_ammo(self, ammo, clip):
        self.current_ammo = ammo
        self.current_clip = clip
        self.update_ammo()

    def use_primary(self):
        if self.character.reloading:
            return False
        shot = True
        if self.character.main:
            if not self.get_ammo()[0]:
                self.play_sound('empty', zone=media.IN_WORLD_AUDIO_ZONE)
                shot = False
                self.character.auto_switch_tool(self)
            if shot:
                seed = random.randint(1, 255)
                if self.character.shoot(seed):
                    pass
                else:
                    self.character.shoot_primary = False
                    shot = False
        if self.character.main and shot:
            self.use_an_ammo()
            self.update_ammo()
        if self.character.main and not self.get_ammo()[0]:
            if self.is_reloadable():
                if self.character.can_shoot_primary():
                    self.character.shoot_primary_held = True
                self.character.reload_next_update = True
            self.character.shoot_primary = False
        if shot:
            if self.play_shoot_animation:
                self.animations['weapon_shoot'].start(self.shoot_interval)
            super(Weapon, self).use_primary()
        return shot

    def can_fire(self):
        if self.character.main:
            return self.get_has_enough_ammo() and not self.character.reloading
        else:
            return True

    def can_draw_ghosting(self):
        return self.current_ammo > 0 or self.current_clip > 0

    def use_an_ammo(self):
        self.current_ammo -= 1

    def get_ammo(self):
        return (
         self.current_ammo, self.current_clip)

    def get_has_enough_ammo(self):
        return self.current_ammo > 0

    def get_ammo_after_reload(self):
        currentAmmo = self.get_ammo()
        if self.clip_reload:
            reloadedAmmo = min(1, currentAmmo[1])
        else:
            reloadedAmmo = min(self.ammo[0] - currentAmmo[0], currentAmmo[1])
        newAmmo = (
         currentAmmo[0] + reloadedAmmo, currentAmmo[1] - reloadedAmmo)
        return newAmmo

    def is_reloadable(self):
        max_ammo, initial_ammo, max_clip, initial_stock, restock_amount = self.ammo
        return self.current_ammo < max_ammo and self.current_clip > 0

    def shoot(self, orientation, seed):
        shoot_bullet(self.character, self.character.world_object.position, orientation, self.block_damage, self.block_penetration, False, seed)
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        return True

    def prep_shoot(self):
        if self.variable_accuracy:
            accuracy_spread_percent = (self.accuracy_spread - self.accuracy_spread_min) / (self.accuracy_spread_max - self.accuracy_spread_min)
            self.accuracy = self.accuracy_min + accuracy_spread_percent * (self.accuracy_max - self.accuracy_min)

    def shot_weapon(self):
        if self.variable_accuracy:
            self.accuracy_spread = min(self.accuracy_spread + self.accuracy_spread_increase_per_shot, self.accuracy_spread_max)
            accuracy_spread_percent = (self.accuracy_spread - self.accuracy_spread_min) / (self.accuracy_spread_max - self.accuracy_spread_min)
            self.accuracy = self.accuracy_min + accuracy_spread_percent * (self.accuracy_max - self.accuracy_min)
        self.muzzle_flash_timer = self.muzzle_flash_duration
        self.muzzle_flash_rotation = random.random() * 360.0

    def draw(self, weapon_display, frustum_check=True):
        if self.muzzle_flash_display:
            if self.muzzle_flash_timer > 0:
                self.muzzle_flash_display.offset_x = self.muzzle_flash_offset.x
                self.muzzle_flash_display.offset_y = self.muzzle_flash_offset.y
                self.muzzle_flash_display.offset_z = self.muzzle_flash_offset.z
                self.muzzle_flash_display.x = weapon_display.x
                self.muzzle_flash_display.y = weapon_display.y
                self.muzzle_flash_display.z = weapon_display.z
                self.muzzle_flash_display.size = weapon_display.size * self.muzzle_flash_scale
                self.muzzle_flash_display.matrix = weapon_display.matrix
                self.muzzle_flash_display.extra_roll = self.muzzle_flash_rotation
                PASSTHROUGH_SHADER.bind()
                self.muzzle_flash_display.draw(frustum_check=frustum_check)
                PASSTHROUGH_SHADER.unbind()

    def draw_muzzle(self, weapon_display, muzzle_offset):
        if self.muzzle_flash_view_display:
            if self.muzzle_flash_timer > 0:
                glTranslatef(muzzle_offset.x, muzzle_offset.y, muzzle_offset.z)
                glRotatef(self.muzzle_flash_rotation, 0.0, 0.0, 1.0)
                self.muzzle_flash_view_display.size = weapon_display.size * self.muzzle_flash_scale
                self.muzzle_flash_view_display.matrix = weapon_display.matrix
                PASSTHROUGH_SHADER.bind()
                self.muzzle_flash_view_display.draw()
                PASSTHROUGH_SHADER.unbind()

    def draw_fps(self, weapon_display):
        self.draw_muzzle(weapon_display, self.muzzle_flash_view_offset)

    def draw_sight(self, weapon_display):
        self.draw_muzzle(weapon_display, self.muzzle_flash_zoomed_view_offset)

    def get_accuracy(self, orientation, projection, window_size):
        if self.variable_accuracy or self.accuracy_zoom != self.accuracy:
            return self.get_variable_accuracy(orientation, projection, window_size)
        else:
            return self.get_static_accuracy()

    def get_variable_accuracy(self, orientation, projection, window_size):
        self.prep_shoot()
        raw_accuracy = self.accuracy_zoom if self.character.zoom and self.accuracy_zoom is not None else self.accuracy
        zoom_modifier = 1 if self.character.zoom else 2
        weapon_accuracy = raw_accuracy * zoom_modifier
        offset_axis = orientation.cross(Vector3(0, 0, -1)).norm()
        offset_dir = (orientation + offset_axis * weapon_accuracy).norm()
        proj = Matrix4()
        for i in xrange(4):
            for j in xrange(4):
                proj[(i, j)] = projection[j * 4 + i]

        rot_angle = math.acos(orientation.dot(Vector3(0, 0, -1)))
        rot_axis = orientation.cross(Vector3(0, 0, -1)).norm()
        rot = Matrix4()
        rot.rotate(math.degrees(rot_angle), rot_axis.get())
        offset_eye_pos = rot.multiply_vector(offset_dir, 0.0)
        offset_clip_pos = proj.multiply_vector(offset_eye_pos, 1.0)
        offset_pixel_pos = ((offset_clip_pos[0] + 1.0) / 2.0 * window_size[0],
         (1.0 - offset_clip_pos[1]) / 2.0 * window_size[1])
        pixels_from_centre = (
         window_size[0] / 2 - offset_pixel_pos[0],
         window_size[1] / 2 - offset_pixel_pos[1])
        return max(math.sqrt(pixels_from_centre[0] ** 2 + pixels_from_centre[1] ** 2) - 3.5, 1)

    def get_static_accuracy(self):
        return self.accuracy_spread * 6
