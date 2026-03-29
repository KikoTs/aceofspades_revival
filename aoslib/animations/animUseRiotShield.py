from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimUseRiotShield(Animation):
    default_length = 0.2

    def __init__(self, length=default_length, speed=None):
        super(AnimUseRiotShield, self).__init__(length, speed)

    def start(self, length=None):
        super(AnimUseRiotShield, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimUseRiotShield, self).update(dt):
            self.position.z = 0.4 - (self.length - self.timer) / self.length * 0.4
            return True
        else:
            return False
