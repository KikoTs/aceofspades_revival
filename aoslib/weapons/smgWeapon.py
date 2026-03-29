from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from aoslib import media

class SMGWeapon(Weapon):
    name = strings.SUB_MACHINE_GUN
    damage = (SMG_DAMAGE_TORSO, SMG_DAMAGE_HEAD, SMG_DAMAGE_ARMS, SMG_DAMAGE_LEGS, SMG_DAMAGE_LEGS)
    block_damage = SMG_DAMAGE_BLOCK
    range = SMG_RANGE
    shoot_sound = BLANK_SOUND
    reload_sound = 'smgreload'
    shoot_interval = SMG_SHOOT_INTERVAL
    reload_time = SMG_RELOAD_TIME
    accuracy_min = SMG_ACCURACY
    accuracy = accuracy_min
    accuracy_max = accuracy_min + SMG_ACCURACY_RANGE
    recoil_up = SMG_RECOIL_UP
    recoil_side = SMG_RECOIL_SIDE
    ammo = (SMG_AMMO_CLIP_SIZE, SMG_AMMO_CLIP_SIZE, SMG_AMMO_MAX, SMG_AMMO_INITIAL_STOCK, SMG_AMMO_RESTOCK_AMOUNT)
    clip_reload = False
    short_ranged_distance = None
    model = [SMG_MODEL]
    view_model = [SMG_VIEW_MODEL]
    casing = SMG_CASING
    tracer = SMG_TRACER
    sight = SMG_SIGHT
    ring = SMG_RING
    image = TOOL_IMAGES[SMG_TOOL]
    sight_pos = (0.0, -0.2, 0.0)
    accuracy_spread_min = SMG_ACCURACY_SPREAD_INITIAL
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + SMG_ACCURACY_SPREAD_RANGE
    accuracy_spread_increase_per_shot = SMG_ACCURACY_SPREAD_INCREASE_PER_SHOT
    accuracy_spread_reduction_speed = SMG_ACCURACY_SPREAD_REDUCTION_SPEED
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SMG)
    muzzle_flash_duration = 0.05
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SMG_VIEW)
    muzzle_flash_offset = Vector3(-12.0, 59.0, -5.0)
    muzzle_flash_view_offset = Vector3(-0.0, 0.12, 0.5)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    shooting = False

    def __init__(self, character):
        super(SMGWeapon, self).__init__(character)
        self.looping_fire_sound = None
        self.play_shoot_sound = False
        self.time_firing = 0.0
        return

    def on_unset(self):
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.time_firing = 0.0
        super(SMGWeapon, self).on_unset()
        return

    def update(self, dt):
        if self.character.can_shoot_primary() and self.can_fire():
            if not self.looping_fire_sound:
                self.looping_fire_sound = self.play_sound('smg_fire_loop', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.shooting = True
        if self.shooting:
            self.time_firing += dt
        if self.time_firing >= SMG_SHOOT_INTERVAL:
            self.play_shoot_sound = False
            self.time_firing -= SMG_SHOOT_INTERVAL
            if not self.character.can_shoot_primary() or not self.can_fire():
                self.shooting = False
            if not self.shooting:
                if self.looping_fire_sound:
                    self.looping_fire_sound.close()
                    self.looping_fire_sound = None
                self.play_sound('smg_fire_tail', position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                self.time_firing = 0.0
        if self.looping_fire_sound:
            pos = self.get_audio_pos()
            if pos:
                self.looping_fire_sound.set_position(*pos)
        return super(SMGWeapon, self).update(dt)
