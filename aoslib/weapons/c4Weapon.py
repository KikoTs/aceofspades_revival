from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from shared.constants import *
from aoslib import strings
from aoslib.animations.animPlaceBlock import *
ghost_c4 = DisplayList(C4_VIEW_MODEL)
ghost_c4.size = 0.06

class C4Weapon(Weapon):
    name = strings.C4
    damage = None
    sight = None
    shoot_sound = None
    model = [C4_MODEL]
    view_model = [C4_DETONATOR_VIEW_MODEL]
    tracer = None
    ammo = (A1745, A1746, None, None, A1747)
    shoot_interval = A1748
    ghost_position = None
    face = 4
    image = TOOL_IMAGES[C4_TOOL]
    has_secondary = True
    model_size = 0.04

    def __init__(self, character):
        super(C4Weapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.18, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.arms_position_offset = Vector3(-0.1, -0.1, 0.2)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)

    def shoot(self, fp3, seed):
        if not self.character.main:
            return
        if not self.ghost_position or self.ghost_face < 0 or self.ghost_face > 5:
            self.play_sound(BUILD_ERROR_SOUND)
            return False
        character = self.character
        scene = self.character.scene
        scene.send_place_c4(self.ghost_position, self.ghost_face)
        self.animations['place_block'].start()
        return True

    def use_secondary(self):
        super(C4Weapon, self).use_secondary()
        character = self.character
        scene = self.character.scene
        character.shoot_secondary = False
        scene.send_detonate_c4()

    def draw_ghosting(self):
        self.ghost_position = None
        can_place_c4, ret = self.character.scene.can_place_object(self.character, A1754, player_min_radius=0, entity_min_radius=1, others_min_radius=0, can_place_vertical=True)
        if not can_place_c4:
            return
        else:
            position, face = ret
            self.ghost_position = position.get()
            self.ghost_face = face
            if self.ghost_face == 0:
                x, y, z = (0.0, 0.5, 0.5)
                o, ox, oy, oz = (90, 0, 0, 1)
            elif self.ghost_face == 1:
                x, y, z = (1.0, 0.5, 0.5)
                o, ox, oy, oz = (-90, 0, 0, 1)
            elif self.ghost_face == 2:
                x, y, z = (0.5, 0.0, 0.5)
                o, ox, oy, oz = (-90, 1, 0, 0)
            elif self.ghost_face == 3:
                x, y, z = (0.5, 1.0, 0.5)
                o, ox, oy, oz = (90, 1, 0, 0)
            elif self.ghost_face == 4:
                x, y, z = (0.5, 0.5, 0.0)
                o, ox, oy, oz = (0, 0, 0, 0)
            elif self.ghost_face == 5:
                x, y, z = (0.5, 0.5, 1.0)
                o, ox, oy, oz = (180, 1, 0, 0)
            else:
                return
            glPushMatrix()
            glTranslatef(position.x + x, -position.z - z, position.y + y)
            glRotatef(o, ox, oy, oz)
            glTranslatef(0, -A1757, 0)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 0.3)
            ghost_c4.draw(frustum_check=False)
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return
