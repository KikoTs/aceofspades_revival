from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimZombieHand(Animation):
    default_length = 0.35

    def __init__(self, length=default_length, speed=None):
        super(AnimZombieHand, self).__init__(length, speed)

    def start(self, length=None):
        super(AnimZombieHand, self).start(length)
        f = self.length
        f2 = f * 6.0
        self.position = Vector3(0.0, -f2 / 3.0, -f2 / 6.5)
        self.orientation = Vector3(-(40.0 + -f * 200.0), 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimZombieHand, self).update(dt):
            f = self.timer
            f2 = f * 6.0
            self.position.y = f2 / 3.0
            self.position.z = f2 / 6.5
            self.orientation.x = 40.0 + -f * 200.0
            return True
        else:
            return False
