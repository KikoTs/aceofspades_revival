from weapon import Weapon
from aoslib.models import *
from shared.constants import *
from . import TOOL_IMAGES
from shared.glm import Vector3
from aoslib.animations.animPlaceBlock import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from aoslib.shaders import *
from aoslib import strings

class RadarStationWeapon(Weapon):
    name = strings.RADAR_STATION
    damage = None
    sight = None
    shoot_sound = None
    model = [RADAR_STATION_BASE_TOOL_MODEL]
    view_model = [RADAR_STATION_BASE_VIEW_MODEL]
    model_size = 0.0175
    view_model_size = 0.03
    ghost_radar_station = [DisplayList(RADAR_STATION_BASE_ENTITY_MODEL)]
    ghost_radar_station_size = 0.03
    ghost_radar_station_position_offsets = []
    tracer = None
    ammo = (A1893, A1894, None, None, A1895)
    shoot_interval = A1897
    ghost_position = None
    image = TOOL_IMAGES[RADAR_STATION_TOOL]

    def __init__(self, character):
        super(RadarStationWeapon, self).__init__(character)
        if character.main:
            self.initial_position[0] = Vector3(-0.1, 0.6, 0.2)
        self.arms_position_offset = Vector3(0.0, -0.66, -0.1)
        self.reset_position(0)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        for display_model_index in range(len(self.ghost_radar_station)):
            self.ghost_radar_station[display_model_index].size = self.ghost_radar_station_size

    def draw_ghosting(self):
        self.ghost_position = None
        can_place_radar_station, ret = self.character.scene.can_place_object(self.character, far_radius=A1896, player_min_radius=1, entity_min_radius=1, others_min_radius=0)
        if not can_place_radar_station:
            return
        else:
            position, face = ret
            self.ghost_position = position.get()
            glPushMatrix()
            glColor4f(1.0, 1.0, 1.0, 1.0)
            glTranslatef(position.x + 0.5, -(position.z + A1902), position.y + 0.5)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 0.3)
            for display_model_index in range(len(self.ghost_radar_station)):
                self.ghost_radar_station[display_model_index].draw(frustum_check=False)

            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return

    def shoot(self, fp3, seed):
        if not self.character.main:
            return False
        if not self.ghost_position:
            return False
        self.character.scene.send_place_radar_station(self.ghost_position)
        self.animations['place_block'].start()
        return True

    def is_available(self):
        return self.get_ammo()[0] > 0
