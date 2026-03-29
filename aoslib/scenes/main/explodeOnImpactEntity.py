from entity import Entity
from aoslib.world import GenericMovement
from shared.glm import Vector3
from aoslib.common import to_pitch_yaw
from aoslib import media
import aoslib.images as aosimages
from aoslib.common import to_pitch_yaw
from shared.common import rotate_2D
from shared.constants import *
import random, math

class ExplodeOnImpactEntity(Entity):
    name = 'ExplodeOnImpactEntity'
    icon = None
    gravity_multiplier = A1648
    fuse_audio_loop = None
    explode_sound = None
    water_explode_sound = None

    def __init__(self, scene, *arg, **kw):
        super(ExplodeOnImpactEntity, self).__init__(scene, *arg, **kw)
        self.world_object = self.scene.world.create_object(GenericMovement, Vector3(0, 0, 0), Vector3(0, 0, 0))
        self.world_object.set_bouncing(False)
        self.world_object.set_stop_on_collision(True)
        self.world_object.set_stop_on_face(True)
        self.world_object.set_gravity_multiplier(self.gravity_multiplier)
        self.pitch, self.yaw = to_pitch_yaw(*Vector3(0, 0, 0).get())
        self.sound = self.scene.media.play(self.fuse_audio_loop, pos=(0, 0, 0), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)

    def update(self, dt):
        scene = self.scene
        self.world_object.update(dt, None)
        pos = self.world_object.position
        if self.sound:
            self.sound.set_position(*pos.get())
        new_pitch, self.yaw = to_pitch_yaw(*self.world_object.velocity.norm().get())
        speed = min(self.world_object.velocity.sq_magnitude(), 1000.0)
        self.pitch = (self.pitch + speed * dt) % 360
        self.display[0].set_rotation(0.0, self.yaw + 180, 0.0)
        self.display[0].add_rotation(-self.pitch, 0.0, 0.0)
        v_x, v_y, v_z = self.world_object.velocity.x, self.world_object.velocity.y, self.world_object.velocity.z
        self.display[0].x = self.world_object.position.x - 0.5
        self.display[0].y = self.world_object.position.y - 0.5
        self.display[0].z = self.world_object.position.z - 0.5
        fire_smoke_offset_forward, fire_smoke_offset_up = rotate_2D(0, 1, -math.radians(self.pitch))
        flat_forward_vector = self.world_object.velocity.copy()
        flat_forward_vector.z = 0.0
        flat_forward_vector = flat_forward_vector.norm()
        fire_smoke_position = self.world_object.position + Vector3(0, 0, -fire_smoke_offset_up) + flat_forward_vector * fire_smoke_offset_forward
        self.create_fire_smoke(fire_smoke_position)
        return

    def set_position(self, x, y, z):
        if self.world_object:
            self.world_object.set_position(Vector3(x, y, z))

    def set_velocity(self, v_x, v_y, v_z):
        if self.world_object:
            self.world_object.set_velocity(Vector3(v_x, v_y, v_z))

    def delete(self):
        if self.sound:
            self.sound.close()
        pos = self.world_object.position
        self.scene.glow_block_particles.create(4, pos)
        solid, color = self.scene.map.get_point(pos.x, pos.y, pos.z)
        r, g, b, a = color
        self.scene.particle_effect_manager.create_particle_effect(None, pos, None, (r, g, b), 10, 1.0, 10.0, 180, 0, True, 1.0, 1.0, 0, 8, 8, random.randint(0, 1), 1, 30, True)
        if pos.z >= MAP_Z - 1:
            self.scene.media.play_pitched(self.water_explode_sound, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        else:
            self.scene.media.play_pitched(self.explode_sound, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        if self.sound:
            self.sound.close()
        super(ExplodeOnImpactEntity, self).delete()
        return

    def create_fire_smoke(self, spawn_position):
        pass
