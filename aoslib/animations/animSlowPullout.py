from aoslib.animations.animation import Animation
from shared.glm import Vector3

class AnimSlowPullout(Animation):
    default_length = 0.5

    def start(self, length=None):
        super(AnimSlowPullout, self).start(length)
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = Vector3(0.0, 0.0, 0.0)

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if super(AnimSlowPullout, self).update(dt):
            if (self.length - self.timer) / self.length > 0.9:
                self.position.y -= 10 * dt / self.length
                self.position.z -= 10 * dt / self.length
            return True
        return False
