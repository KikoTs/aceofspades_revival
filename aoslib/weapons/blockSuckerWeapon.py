from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings, media
from tool import Tool
from aoslib import media
from aoslib.animations.animBlockSucker import *

class BlockSuckerWeapon(Weapon):
    name = strings.BLOCK_SUCKER
    damage = None
    sight = None
    shoot_sound = None
    accuracy = A1981
    recoil_up = A1982
    recoil_side = A1983
    reload_time = 1
    clip_reload = False
    shoot_interval = A1984
    model = [BLOCKSUCKER_MODEL]
    view_model = [BLOCKSUCKER_VIEW_MODEL]
    tracer = None
    image = TOOL_IMAGES[BLOCK_SUCKER_TOOL]
    noof_primary_blocks = 1
    engine_sound = None
    current_ammo = 1
    draw_ammo = False
    warm_up_timer = 0
    warm_up_delay = A1991
    play_shoot_animation = False
    start_sound = None
    active_loop_sound = None
    stop_sound = None
    block_sucker_state = A1998
    reactivate_delay_timer = 0
    model_size = 0.05
    view_model_size = 0.05

    def __init__(self, character):
        super(BlockSuckerWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.0, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(-0.3, -0.1, 0.4)
        self.animations['sucker_active'] = AnimBlockSucker(self.warm_up_delay)

    def can_shoot_primary(self):
        if self.reactivate_delay_timer > 0 or self.is_active():
            return False
        return super(BlockSuckerWeapon, self).can_shoot_primary()

    def on_start_primary(self):
        super(BlockSuckerWeapon, self).on_start_primary()
        self.set_state_warming_up()

    def on_stop_primary(self):
        super(BlockSuckerWeapon, self).on_stop_primary()
        self.set_state_inactive()
        self.reactivate_delay_timer = A1992
        return True

    def shoot(self, fp3, seed):
        if self.character.main and self.block_sucker_state == A2000:
            self.character.scene.send_block_sucker_state(self.character.parent, self.block_sucker_state, True)
        return True

    def update(self, dt):
        if self.character.main and self.reactivate_delay_timer > 0:
            self.reactivate_delay_timer -= dt
        if self.block_sucker_state == A1999:
            self.warm_up_timer += dt
            if self.warm_up_timer >= self.warm_up_delay:
                self.set_state_full_power()
        if self.block_sucker_state == A2000:
            if not self.active_loop_sound or not self.active_loop_sound.is_playing():
                if not self.start_sound or not self.start_sound.is_playing():
                    self.active_loop_sound = self.play_sound(A2966, position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            if self.character.main and self.shoot_delay <= 0:
                self.use_primary()
        self.animations['sucker_active'].update_state(self.block_sucker_state, self.warm_up_timer)
        pos = self.get_audio_pos()
        if pos:
            if self.start_sound and self.start_sound.is_playing():
                self.start_sound.set_position(*pos)
            if self.active_loop_sound and self.active_loop_sound.is_playing():
                self.active_loop_sound.set_position(*pos)
            if self.stop_sound and self.stop_sound.is_playing():
                self.stop_sound.set_position(*pos)
        return super(BlockSuckerWeapon, self).update(dt)

    def set_state_inactive(self):
        if self.block_sucker_state != A1998:
            if self.start_sound and self.start_sound.is_playing():
                self.start_sound.close()
            if self.active_loop_sound and self.active_loop_sound.is_playing():
                self.active_loop_sound.close()
                self.active_loop_sound = None
            self.animations['sucker_active'].stop()
            if self.block_sucker_state == A2000:
                self.stop_sound = self.play_sound(A2967, position=self.get_audio_pos(), loops=1, zone=media.IN_WORLD_AUDIO_ZONE)
            self.block_sucker_state = A1998
            if self.character.main:
                self.character.scene.send_block_sucker_state(self.character.parent, A1998)
        return

    def set_state_warming_up(self):
        if self.block_sucker_state != A1999:
            self.block_sucker_state = A1999
            self.warm_up_timer = 0
            if self.active_loop_sound and self.active_loop_sound.is_playing():
                self.active_loop_sound.close()
                self.active_loop_sound = None
            if self.stop_sound and self.stop_sound.is_playing():
                self.stop_sound.close()
            self.start_sound = self.play_sound(A2965, position=self.get_audio_pos(), loops=1, zone=media.IN_WORLD_AUDIO_ZONE)
            if self.character.main:
                self.character.scene.send_block_sucker_state(self.character.parent, A1999)
        return

    def set_state_full_power(self):
        if self.block_sucker_state != A2000:
            self.block_sucker_state = A2000
            if self.character.main:
                self.character.scene.send_block_sucker_state(self.character.parent, A2000)

    def set_state(self, new_state):
        if new_state == A1998:
            self.set_state_inactive()
        elif new_state == A1999:
            self.set_state_warming_up()
        elif new_state == A2000:
            self.set_state_full_power()

    def on_sucked_up_block(self):
        self.play_sound(A2968, position=self.get_audio_pos(), loops=1, zone=media.IN_WORLD_AUDIO_ZONE)

    def on_set(self):
        Weapon.on_set(self)

    def on_unset(self):
        self.set_state_inactive()
        super(BlockSuckerWeapon, self).on_unset()

    def use_an_ammo(self):
        pass

    def set_ammo(self, ammo, clip):
        pass

    def restock(self, type=None):
        self.update_ammo()

    def get_has_enough_ammo(self):
        return True

    def is_reloadable(self):
        return False
