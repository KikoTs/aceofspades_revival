from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimPlaceBlock(Animation):
    default_length = 0.5

    def start(self, length=None):
        super(AnimPlaceBlock, self).start(length)
        self.position = Vector3(-self.length, -self.length, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimPlaceBlock, self).update(dt):
            self.position.x += dt
            self.position.y += dt
            return True
        else:
            return False
