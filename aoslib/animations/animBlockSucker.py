from aoslib.animations.animation import Animation
from shared.glm import Vector3
from shared.constants import *
import math, random

class AnimBlockSucker(Animation):
    horiz_sin = 0
    vert_sin = 0
    warm_up_start_amplitude = 0.06
    full_power_amplitude = 0.02
    block_sucker_state = A1998
    warm_up_timer = 0
    current_shake_amplitude = 0
    in_active_settledown_timer = 0
    is_active_settledown_duration = 1
    in_active_settledown_start_amplitude = 0

    def __init__(self, warm_up_duration):
        super(AnimBlockSucker, self).__init__(1, 1, False)
        self.warm_up_duration = warm_up_duration

    def start(self, length=None):
        pass

    def update_state(self, block_sucker_state, warm_up_timer):
        self.warm_up_timer = warm_up_timer
        if self.block_sucker_state != block_sucker_state:
            self.block_sucker_state = block_sucker_state
            if self.block_sucker_state == A1998:
                if self.is_playing():
                    self.in_active_settledown_start_amplitude = self.current_shake_amplitude
                    self.in_active_settledown_timer = self.is_active_settledown_duration
            elif not self.is_playing():
                self.playing = True
                self.position = Vector3(0.0, 0.0, 0.0)
                self.orientation = Vector3(0.0, 0.0, 0.0)
                self.horiz_sin = 0
                self.vert_sin = 0

    def stop(self):
        self.update_state(A1998, 0)

    def update(self, dt):
        super(AnimBlockSucker, self).update(dt)
        if self.block_sucker_state == A1998:
            self.in_active_settledown_timer -= dt
            if self.in_active_settledown_timer <= 0:
                self.playing = False
                return False
            self.current_shake_amplitude = self.in_active_settledown_start_amplitude * (self.in_active_settledown_timer / self.is_active_settledown_duration)
        elif self.block_sucker_state == A1999:
            warm_up_duration_half = self.warm_up_duration / 2.0
            if self.warm_up_timer < warm_up_duration_half:
                self.current_shake_amplitude = self.warm_up_start_amplitude * (self.warm_up_timer / warm_up_duration_half)
            else:
                self.current_shake_amplitude = self.warm_up_start_amplitude - (self.warm_up_start_amplitude - self.full_power_amplitude) * ((self.warm_up_timer - warm_up_duration_half) / (self.warm_up_duration - warm_up_duration_half))
        elif self.block_sucker_state == A2000:
            self.current_shake_amplitude = self.full_power_amplitude
        self.horiz_sin += dt * (15 + random.random() * 10)
        self.vert_sin += dt * (20 + random.random() * 15)
        horiz = math.sin(self.horiz_sin) * self.current_shake_amplitude
        vert = math.sin(self.vert_sin) * self.current_shake_amplitude
        self.position.x = horiz
        self.position.y = vert
        self.position.z = 0
        return True
