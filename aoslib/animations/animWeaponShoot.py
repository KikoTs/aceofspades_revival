from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimWeaponShoot(Animation):
    default_length = 0.2

    def __init__(self, length=default_length, speed=None):
        super(AnimWeaponShoot, self).__init__(length, speed)

    def start(self, length=None):
        super(AnimWeaponShoot, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimWeaponShoot, self).update(dt):
            if self.timer > 0:
                f = -self.timer / 32.0
                f2 = f * 10
                self.position.x = f2
                self.position.y = f2
                self.position.z = f2
                self.orientation.x = f * 280
            return True
        return False
