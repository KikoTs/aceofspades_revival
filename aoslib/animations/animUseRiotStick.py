from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimUseRiotStick(Animation):
    default_length = 0.2

    def __init__(self, length=default_length, speed=None):
        super(AnimUseRiotStick, self).__init__(length, speed)

    def start(self, length=None):
        super(AnimUseRiotStick, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimUseRiotStick, self).update(dt):
            self.position.z = 0.4 - (self.length - self.timer) / self.length * 0.4
            self.position.y = -0.5 + (self.length - self.timer) / self.length * 0.5
            self.orientation.x = 120.0 - (self.length - self.timer) / self.length * 120.0
            return True
        else:
            return False
