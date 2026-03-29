from drawItem import DrawItem
from entity import Entity
from aoslib.world import GenericMovement
from aoslib.draw import DisplayList
from shared.glm import Vector3
from aoslib.shaders import *
from aoslib.models import *
from aoslib.common import to_pitch_yaw
from aoslib import media
from shared.constants import *
import random

class Drill(Entity):
    name = 'Drill'
    icon = None
    size = 0.08
    model = [DRILL_MODEL]
    model_position_offsets = []
    drilling_loop_timeout = A1509
    time_drilling = 0.0
    drilling_loop_sound = None
    lifespan = A1507

    def __init__(self, scene, *arg, **kw):
        super(Drill, self).__init__(scene, *arg, **kw)
        self.world_object = self.scene.world.create_object(GenericMovement, Vector3(0, 0, 0), Vector3(0, 0, 0) * A1493)
        self.world_object.set_gravity_multiplier(A1494)
        self.world_object.set_bouncing(False)
        self.world_object.set_stop_on_collision(True)
        self.pitch, self.yaw = to_pitch_yaw(*Vector3(0, 0, 0).get())
        self.sound = self.scene.media.play('drill_projectile', pos=(0, 0, 0), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
        self.lifespan = A1507
        self.roll = 0
        self.time_drilling = 0.0
        self.drilling_loop_sound = None
        return

    def update(self, dt):
        scene = self.scene
        old_velocity = self.world_object.velocity.copy()
        if self.world_object.update(dt, None):
            self.world_object.velocity.set_vector(old_velocity)
        pos = self.world_object.position
        self.roll += 10.0
        if self.lifespan > 0:
            self.lifespan = max(self.lifespan - dt, 0)
        if self.sound:
            self.sound.set_position(*pos.get())
        self.pitch, self.yaw = to_pitch_yaw(*self.world_object.velocity.norm().get())
        self.display[0].set_rotation(0.0, self.yaw + 180, 0.0)
        self.display[0].add_rotation(-self.pitch, 0.0, 0.0)
        self.display[0].add_rotation(0.0, 0.0, -self.roll)
        self.display[0].x = self.world_object.position.x - 0.5
        self.display[0].y = self.world_object.position.y - 0.5
        self.display[0].z = self.world_object.position.z - 0.5
        if self.drilling_loop_sound:
            self.time_drilling -= dt
            if self.time_drilling <= 0.0:
                self.drilling_loop_sound.close()
                self.drilling_loop_sound = None
            else:
                self.drilling_loop_sound.set_position(*pos.get())
        elif self.time_drilling > 0.0:
            self.drilling_loop_sound = self.scene.media.play('drill_loop', pos=pos.get(), zone=media.IN_WORLD_AUDIO_ZONE)
        return

    def get_lifespan(self):
        return self.lifespan

    def set_position(self, x, y, z):
        if self.world_object:
            self.world_object.set_position(Vector3(x, y, z))

    def set_velocity(self, v_x, v_y, v_z):
        if self.world_object:
            self.world_object.set_velocity(Vector3(v_x, v_y, v_z))

    def do_drill(self, position):
        self.scene.media.play(DRILL_DRILLING_EXPLODE_SOUND, pos=position, zone=media.IN_WORLD_AUDIO_ZONE)
        self.time_drilling = self.drilling_loop_timeout

    def delete(self):
        pos = self.world_object.position
        if pos.z >= MAP_Z - 1:
            self.scene.media.play_pitched(DRILL_WATER_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        else:
            self.scene.media.play_pitched(DRILL_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        if self.sound:
            self.sound.close()
        if self.drilling_loop_sound:
            self.drilling_loop_sound.close()
            self.drilling_loop_sound = None
        pos = Vector3(self.display[0].x, self.display[0].y, self.display[0].z)
        self.scene.glow_block_particles.create(8, pos)
        self.scene.particle_effect_manager.create_particle_effect(None, pos, None, (96,
                                                                                    96,
                                                                                    96), 10, 1.5, 5.0)
        self.scene.explode_display(self.display[0], 1.0, 3)
        super(Drill, self).delete()
        return
