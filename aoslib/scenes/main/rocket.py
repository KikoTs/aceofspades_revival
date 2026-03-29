from drawItem import DrawItem
from entity import Entity
from aoslib.world import GenericMovement
from aoslib.draw import DisplayList, create_particle_spawn_point
from shared.glm import Vector3
from aoslib.shaders import *
from aoslib.models import *
from aoslib.common import to_pitch_yaw
from aoslib import media
import aoslib.images as aosimages
from aoslib.common import to_pitch_yaw
from shared.constants import *
import random

class Rocket(Entity):
    name = 'Rocket'
    icon = None
    size = 0.02
    model = [ROCKET_MODEL]
    model_position_offsets = []
    rocket_type = 'rpg'
    shoot_sound_played = True

    def __init__(self, scene, *arg, **kw):
        super(Rocket, self).__init__(scene, *arg, **kw)
        self.world_object = self.scene.world.create_object(GenericMovement, Vector3(0, 0, 0), Vector3(0, 0, 0) * A1397)
        self.world_object.set_gravity_multiplier(A1398)
        self.world_object.set_bouncing(False)
        self.world_object.set_stop_on_collision(False)
        self.pitch, self.yaw = to_pitch_yaw(*Vector3(0, 0, 0).get())
        if self.player and self.player.tool_id == RPG_TOOL:
            self.rocket_type = 'rpg'
            self.sound = self.scene.media.play('rocket_projectile', pos=(0, 0, 0), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
        else:
            self.rocket_type = 'rocket_turret'
            self.sound = self.scene.media.play('turr_rocket_projectile', pos=(0, 0,
                                                                              0), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
        self.flame_dt = self.smoke_dt = 0.0

    def update(self, dt):
        scene = self.scene
        self.world_object.update(dt, None)
        pos = self.world_object.position
        if self.sound:
            self.sound.set_position(*pos.get())
        self.pitch, self.yaw = to_pitch_yaw(*self.world_object.velocity.norm().get())
        self.display[0].set_rotation(0.0, self.yaw + 180, 0.0)
        self.display[0].add_rotation(-self.pitch, 0.0, 0.0)
        v_x, v_y, v_z = self.world_object.velocity.x, self.world_object.velocity.y, self.world_object.velocity.z
        smoke_velocity = Vector3(v_x, v_y, v_z).norm() * (dt * A1397) * 0.005
        smoke_velocity.x *= ROCKET_SMOKE_VELOCITY_MULTIPLIER + random.uniform(ROCKET_SMOKE_VELOCITY_RANDOM_MIN_MULTIPLIER, ROCKET_SMOKE_VELOCITY_RANDOM_MAX_MULTIPLIER)
        smoke_velocity.y *= ROCKET_SMOKE_VELOCITY_MULTIPLIER + random.uniform(ROCKET_SMOKE_VELOCITY_RANDOM_MIN_MULTIPLIER, ROCKET_SMOKE_VELOCITY_RANDOM_MAX_MULTIPLIER)
        smoke_velocity.z *= ROCKET_SMOKE_VELOCITY_MULTIPLIER + random.uniform(ROCKET_SMOKE_VELOCITY_RANDOM_MIN_MULTIPLIER, ROCKET_SMOKE_VELOCITY_RANDOM_MAX_MULTIPLIER)
        smoke_pos = Vector3(pos.x, pos.y, pos.z)
        smoke_pos.z += 0.5
        smoke_decay = random.randint(0, ROCKET_SMOKE_DECAY_RATE_MAX) - ROCKET_SMOKE_DECAY_RATE_MIN
        if smoke_decay == 0:
            smoke_decay = ROCKET_SMOKE_DECAY_RATE_DEFAULT
        self.scene.particle_effect_manager.create_particle_effect(aosimages.particle_smoke_trail, smoke_pos, smoke_velocity, (255,
                                                                                                                              255,
                                                                                                                              255), 1, 0.0, random.uniform(ROCKET_SMOKE_INITIAL_SIZE_RANDOM_MIN, ROCKET_SMOKE_INITIAL_SIZE_RANDOM_MAX), random.randint(ROCKET_SMOKE_INITIAL_ROTATION_RANDOM_MIN, ROCKET_SMOKE_INITIAL_ROTATION_RANDOM_MAX), 0, False, smoke_decay, ROCKET_SMOKE_LIFETIME, 1, 8, 8, 1, 0, 60, False)
        self.display[0].x = self.world_object.position.x - 0.5
        self.display[0].y = self.world_object.position.y - 0.5
        self.display[0].z = self.world_object.position.z - 0.5
        return

    def set_position(self, x, y, z):
        if self.world_object:
            self.world_object.set_position(Vector3(x, y, z))
            if self.rocket_type == 'rocket_turret' and not self.shoot_sound_played:
                self.scene.media.play_pitched(ROCKET_TURRET_SHOOT_SOUND, pos=(x, y, z), zone=media.IN_WORLD_AUDIO_ZONE)

    def set_velocity(self, v_x, v_y, v_z):
        if self.world_object:
            self.world_object.set_velocity(Vector3(v_x, v_y, v_z))

    def delete(self):
        pos = self.world_object.position
        self.scene.glow_block_particles.create(8, pos)
        solid, color = self.scene.map.get_point(pos.x, pos.y, pos.z)
        r, g, b, a = color
        self.scene.particle_effect_manager.create_particle_effect(None, pos, None, (r, g, b), 10, 1.0, 10.0, 180, 0, True, 1.0, 1.0, 0, 8, 8, random.randint(0, 1), 1, 30, True)
        if self.rocket_type == 'rpg':
            if pos.z >= MAP_Z - 1:
                self.scene.media.play_pitched(ROCKET_WATER_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
            else:
                self.scene.media.play_pitched(ROCKET_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        elif self.rocket_type == 'rocket_turret':
            if pos.z >= MAP_Z - 1:
                self.scene.media.play_pitched(TURRET_ROCKET_WATER_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
            else:
                self.scene.media.play_pitched(TURRET_ROCKET_EXPLODE_SOUND, pos=(pos.x, pos.y, pos.z), zone=media.IN_WORLD_AUDIO_ZONE)
        if self.sound:
            self.sound.close()
        super(Rocket, self).delete()
        return
