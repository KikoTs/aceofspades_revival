from shared.glm import Vector3

class Animation(object):
    playing = False
    stop_on_end = True

    def __init__(self, length=None, speed=None, stop_on_end=True):
        self.length = 0.0
        self.timer = 0.0
        self.speed = 1.0
        self.position = Vector3()
        self.orientation = Vector3()
        self.stop_on_end = stop_on_end
        if speed:
            self.speed = speed
        if length:
            self.length = length

    def start(self, length=None):
        self.playing = True
        if length:
            self.timer = length
        else:
            self.timer = self.length

    def stop(self):
        self.playing = False
        self.timer = 0

    def update(self, dt):
        dt = min(self.timer, dt * self.speed)
        if self.timer > 0.0:
            self.timer -= dt
            return True
        else:
            if self.stop_on_end:
                self.stop()
            return False

    def get_position(self):
        return self.position.copy()

    def get_orientation(self):
        return self.orientation.copy()

    def set_position(self, position):
        self.position = position.copy()

    def set_orientation(self, orientation):
        self.orientation = orientation.copy()

    def get_speed(self, speed):
        return self.speed

    def set_speed(self, speed):
        self.speed = speed

    def is_playing(self):
        if self.stop_on_end:
            return self.timer > 0
        else:
            return self.playing
