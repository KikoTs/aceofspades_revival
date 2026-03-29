from entity import Entity
from aoslib.models import *
from aoslib import image
from shared.glm import Vector3
from shared.constants import *
from aoslib import media
from shared.common import distance_vector_3d_squared
from aoslib.text import ammo_font

class RocketTurret(Entity):
    name = 'RocketTurret'
    icon = image.load('marker_turret_16', center=True)
    icon_scale = 1.0
    size = A1610
    old_pitch = old_yaw = pitch = yaw = 0.0
    model = [TURRET_BASE_ENTITY_MODEL, TURRET_BALL_ENTITY_MODEL, TURRET_GUN_ENTITY_MODEL]
    model_position_offsets = []
    aim_loop_sound = None
    aiming = False
    aiming_tolerance_timer = aiming_tolerance = 0.2
    target_id = None
    world_object = None
    ammo = A1615

    def __init__(self, scene, *arg, **kw):
        super(RocketTurret, self).__init__(scene, *arg, **kw)
        self.world_object = None
        self.pitch = 0.0
        self.pitch_delta = -30
        self.yaw = 0.0
        self.model_position_offsets[0] = Vector3(0.0, 0.0, A1612)
        self.model_position_offsets[1] = Vector3(0.0, 0.0, A1613)
        self.model_position_offsets[2] = Vector3(0.0, 0.0, A1614)
        self.display[1].set_rotation(0.0, 45.0, 0.0)
        self.display[2].set_rotation(0.0, 45.0, 0.0)
        self.display[2].add_rotation(-45.0, 0.0, 0.0)
        return

    def initialize(self, *arg, **kw):
        Entity.initialize(self, *arg, **kw)

    def update(self, dt):
        super(RocketTurret, self).update(dt)
        if self.ammo is not None:
            display_ammo_text = A1626 == 0
            if self.scene.character is not None and display_ammo_text is False and self.scene.player is not None and self.team is self.scene.player.team:
                character = self.scene.character
                character_pos = character.world_object.position
                turret_pos = self.get_position()
                dist_squared = distance_vector_3d_squared(character_pos, turret_pos)
                radius_squared = A1626 * A1626
                if dist_squared < radius_squared:
                    display_ammo_text = True
            if self.text3d is not None:
                text_position = self.get_position()
                if display_ammo_text:
                    self.update_3dText(self.ammo, Vector3(text_position.x, text_position.y, text_position.z - 1.0))
                else:
                    self.text3d.set_text('')
        if self.player:
            if abs(self.pitch - self.old_pitch) / dt > A1607 * 10 or abs(self.yaw - self.old_yaw) / dt > A1607 * 10:
                self.aiming = True
                self.aiming_tolerance_timer = self.aiming_tolerance
            elif self.aiming_tolerance_timer > 0:
                self.aiming_tolerance_timer -= dt
            else:
                self.aiming = False
            self.old_pitch = self.pitch
            self.old_yaw = self.yaw
            position = (
             self.display[0].x, self.display[0].y, self.display[0].z)
            if self.aiming:
                if not self.aim_loop_sound or not self.aim_loop_sound.is_playing():
                    self.player.scene.media.play('turret_aim_start', pos=position, zone=media.IN_WORLD_AUDIO_ZONE)
                    self.aim_loop_sound = self.player.scene.media.play('turret_aiming_lp', pos=position, loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
                else:
                    self.aim_loop_sound.set_position(*position)
            elif self.aim_loop_sound and self.aim_loop_sound.is_playing():
                self.player.scene.media.play('turret_aim_stop', pos=position, zone=media.IN_WORLD_AUDIO_ZONE)
                self.aim_loop_sound.close()
        self.display[1].set_rotation(0.0, self.yaw, 0.0)
        self.display[2].set_rotation(0.0, self.yaw, 0.0)
        self.display[2].add_rotation(self.pitch, 0.0, 0.0)
        return

    def set_position(self, x, y, z):
        return super(RocketTurret, self).set_position(x - 0.5, y - 0.5, z)

    def set_pitch(self, pitch):
        self.pitch = pitch

    def set_yaw(self, yaw):
        self.yaw = yaw

    def on_delete(self):
        if self.text3d is not None:
            self.scene.text3d.remove_text(self.id)
        if self.aim_loop_sound and self.aim_loop_sound.is_playing():
            self.aim_loop_sound.close()
        position = self.display[0]
        if self.player:
            if position.z >= MAP_Z - 2:
                sound_name = 'turret_explode_water'
            else:
                sound_name = 'turret_explode'
            self.player.scene.media.play(sound_name, pos=(position.x, position.y, position.z), zone=media.IN_WORLD_AUDIO_ZONE)
        super(RocketTurret, self).on_delete()
        for display in self.display[:]:
            pos = Vector3(self.display[0].x, self.display[0].y, self.display[0].z)
            self.scene.glow_block_particles.create(8, pos)
            self.scene.particle_effect_manager.create_particle_effect(None, pos, None, (96,
                                                                                        96,
                                                                                        96), 10, 1.5, 5.0)
            self.scene.explode_display(display, 1.0, 5)

        return

    def set_target(self, target_id):
        if self.target_id != target_id:
            if self.player:
                position = (
                 self.display[0].x, self.display[0].y, self.display[0].z)
                if target_id == None:
                    self.player.scene.media.play('turret_lockoff', pos=position, zone=media.IN_WORLD_AUDIO_ZONE)
                else:
                    self.player.scene.media.play('turret_lockon', pos=position, zone=media.IN_WORLD_AUDIO_ZONE)
            self.target_id = target_id
        return

    def set_ammo(self, ammo):
        self.ammo = ammo
        if self.text3d is None:
            self.create_3dText()
            self.text3d.set_font(ammo_font)
        if self.ammo > 0:
            self.text3d.set_color(ENOUGH_AMMO_COLOR)
        else:
            self.text3d.set_color(NOT_ENOUGH_AMMO_COLOR)
        return

    def draw_on_minimap(self, player):
        if player is not None and self.team is player.team:
            return super(RocketTurret, self).draw_on_minimap(player)
        else:
            return False
            return
