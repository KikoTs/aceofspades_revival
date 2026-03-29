from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimThrowGrenade(Animation):
    default_length = 0.5

    def __init__(self, length=default_length, speed=None, stop_on_end=True):
        super(AnimThrowGrenade, self).__init__(length, speed, stop_on_end)

    def start(self, length=None):
        super(AnimThrowGrenade, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimThrowGrenade, self).update(dt):
            value = self.length - self.timer
            self.position.x = -value * 1.5
            self.position.y = value * 0.5
            self.orientation.x = value * -40
            return True
        else:
            return False
