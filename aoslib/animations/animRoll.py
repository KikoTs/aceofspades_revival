from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimRoll(Animation):
    default_length = 1.0

    def __init__(self, length=default_length, speed=None):
        super(AnimRoll, self).__init__(length, speed)

    def start(self, length=None):
        super(AnimRoll, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimRoll, self).update(dt):
            self.orientation.z = (self.orientation.z + dt * 360.0 / self.length) % 360
            return True
        else:
            return False
