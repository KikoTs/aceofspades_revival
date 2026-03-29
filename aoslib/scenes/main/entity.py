from drawItem import DrawItem
from aoslib.common import to_float_color
from aoslib.draw import DisplayList
from aoslib.models import *
from aoslib.shaders import *
from shared.glm import Vector3
import math
from aoslib.hud.text3d import Text3D
from aoslib.kv6 import set_kv6_default_color
from aoslib import media
from aoslib import image

class Entity(DrawItem):
    visible = True
    player = None
    alpha = None
    team = None
    controllable = False
    shoot_primary = shoot_secondary = False
    minimap = False
    icon = None
    icon_scale = 1.0
    height_icon = image.load('minimap_height_indicator', center=True)
    face = 4
    velocity = Vector3()
    minimap = False
    size = 1.0
    spot_shadow_pos_offset = (0.0, 0.0, 0.0)
    spot_shadow_size = 1.0
    size = 1.0
    type_id = None

    def initialize(self, entity_id, team, player, spawned):
        self.spawned = spawned
        self.scene.entities[entity_id] = self
        self.id = entity_id
        self.color = to_float_color((0, 0, 0))
        self.set_team(team)
        self.set_player(player)
        self.create_display()
        self.text3d = None
        return

    def create_3dText(self):
        if self.scene is None or self.id is None:
            return
        if self.world_object is None:
            position = self.get_position()
        else:
            position = self.world_object.position
        self.text3d = Text3D('.', position, 0.005, disable_depth_test=True)
        self.scene.text3d.add_text(self.id, self.text3d)
        return

    def update_3dText(self, float_value, position):
        if self.text3d is None:
            return
        else:
            self.text3d.position = position
            self.text3d.set_text(str(('{0:.0f}').format(math.ceil(float_value))))
            return

    def post_initialize(self):
        pass

    def delete(self):
        if self.deleted:
            return
        DrawItem.delete(self)
        self.scene.entities.pop(self.id)

    def hit(self, x, y, z, type):
        from aoslib.gfx.particleEffectManager import ParticleEffectManager
        self.scene.particle_effect_manager.create_particle_effect(None, Vector3(x, y, z), None, (127,
                                                                                                 127,
                                                                                                 127), 5, 0.25, size=2.0)
        return

    def create_display(self):
        self.display = []
        self.model_position_offsets = []
        for model_index in range(len(self.model)):
            self.display.append(DisplayList(self.model[model_index]))
            self.display[model_index].size = self.size
            self.model_position_offsets.append(Vector3(0.0, 0.0, 0.0))

    def set_face(self, face):
        self.face = face
        if self.face == 0:
            self.rotate(Vector3(0, 0, 1), 90)
        if self.face == 1:
            self.rotate(Vector3(0, 0, 1), -90)
        if self.face == 2:
            self.rotate(Vector3(1, 0, 0), -90)
        if self.face == 3:
            self.rotate(Vector3(1, 0, 0), 90)
        if self.face == 5:
            self.rotate(Vector3(1, 0, 0), 180)

    def set_position(self, x, y, z):
        for model_index in range(len(self.model)):
            if self.face == 0:
                dx = -0.5 + self.model_position_offsets[model_index].z
                dy = self.model_position_offsets[model_index].x
                dz = self.model_position_offsets[model_index].y
            elif self.face == 1:
                dx = 0.5 - self.model_position_offsets[model_index].z
                dy = self.model_position_offsets[model_index].x
                dz = self.model_position_offsets[model_index].y
            elif self.face == 2:
                dx = self.model_position_offsets[model_index].y
                dy = -0.5 + self.model_position_offsets[model_index].z
                dz = self.model_position_offsets[model_index].x
            elif self.face == 3:
                dx = self.model_position_offsets[model_index].y
                dy = 0.5 - self.model_position_offsets[model_index].z
                dz = self.model_position_offsets[model_index].x
            elif self.face == 4:
                dx = self.model_position_offsets[model_index].x
                dy = self.model_position_offsets[model_index].y
                dz = 0.5 - self.model_position_offsets[model_index].z
            elif self.face == 5:
                dx = self.model_position_offsets[model_index].x
                dy = self.model_position_offsets[model_index].y
                dz = -0.5 + self.model_position_offsets[model_index].z
            self.display[model_index].x = x + dx
            self.display[model_index].y = y + dy
            self.display[model_index].z = z - dz

    def set_velocity(self, v_x, v_y, v_z):
        self.velocity = Vector3(v_x, v_y, v_z)

    def set_forward_vector(self, forward_x, forward_y, forward_z):
        pass

    def set_color(self, r, g, b):
        self.color = to_float_color((r, g, b))

    def get_spot_shadow_pos(self):
        return Vector3(self.display[0].x + self.spot_shadow_pos_offset[0], self.display[0].y + self.spot_shadow_pos_offset[1], self.display[0].z + self.spot_shadow_pos_offset[2])

    def get_position(self):
        return Vector3(self.display[0].x, self.display[0].y, self.display[0].z)

    def set_player(self, player):
        if self.player is player:
            return
        else:
            if self.controllable:
                if self.player:
                    self.player.character.set_entity(None)
                if player:
                    player.character.set_entity(self)
            self.player = player
            return

    def set_team(self, team):
        self.team = team

    def play_sound(self, value, volume=0.75, loops=1, zone=media.DEFAULT_AUDIO_ZONE):
        pos = self.get_position()
        sound = self.scene.media.play(value, volume=volume, loops=loops, pos=(
         pos.x, pos.y, pos.z), zone=zone)
        return sound

    def draw(self):
        if self.team:
            set_kv6_default_color(*to_float_color(self.team.color))
        else:
            set_kv6_default_color(*to_float_color(self.color))
        if self.alpha is not None:
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, self.alpha)
            self.draw_display()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
        else:
            self.draw_display()
        set_kv6_default_color(0.0, 0.0, 0.0)
        return

    def draw_display(self):
        for model_index in range(len(self.model)):
            self.display[model_index].draw()

    def set_primary_shoot(self, character, value):
        shoot_primary = value

    def set_secondary_shoot(self, character, value):
        shoot_secondary = value

    def set_packet(self, packet):
        pass

    def get_hud_icon(self):
        return

    def rotate(self, axis, angle, index=None):
        if index == None:
            for model_index in range(len(self.model)):
                self.display[model_index].rotate(angle, axis.get())

        else:
            self.display[index].rotate(angle, axis.get())
        return

    def set_fuse(self, fuse):
        pass

    def set_ammo(self, ammo):
        pass

    def set_target(self, target_id):
        pass

    def set_pitch(self, pitch):
        pass

    def set_yaw(self, yaw):
        pass

    def draw_on_minimap(self, player):
        return True
