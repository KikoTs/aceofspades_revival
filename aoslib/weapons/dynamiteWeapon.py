from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from pyglet.gl import *
from shared.constants import *
from aoslib import strings
from aoslib.animations.animPlaceBlock import *
ghost_dynamite = DisplayList(DYNAMITE_VIEW_MODEL)
ghost_dynamite.size = 0.06

class DynamiteWeapon(Weapon):
    name = strings.DYNAMITE_TOOL
    damage = None
    sight = None
    shoot_sound = None
    model = [DYNAMITE_MODEL]
    view_model = [DYNAMITE_VIEW_MODEL]
    tracer = None
    ammo = (A1627, A1628, None, None, A1629)
    shoot_interval = A1630
    ghost_position = None
    face = 4
    image = TOOL_IMAGES[DYNAMITE_TOOL]

    def __init__(self, character):
        super(DynamiteWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.18, 0.0)
                self.initial_orientation[model_index] = Vector3(-20.0, 200.0, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.arms_position_offset = Vector3(0.0, -0.18, 0.0)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_DYNAMITE)

    def shoot(self, fp3, seed):
        if not self.character.main:
            return
        if not self.ghost_position or self.ghost_face < 0 or self.ghost_face > 5:
            self.play_sound(BUILD_ERROR_SOUND)
            return False
        character = self.character
        scene = self.character.scene
        scene.send_place_dynamite(self.ghost_position, self.ghost_face)
        self.animations['place_block'].start()
        return True

    def draw_ghosting(self):
        self.ghost_position = None
        can_place_dynamite, ret = self.character.scene.can_place_object(self.character, A1637, player_min_radius=0, entity_min_radius=1, others_min_radius=0, can_place_vertical=True)
        if not can_place_dynamite:
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
            glTranslatef(0, -A1640, 0)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 0.3)
            ghost_dynamite.draw(frustum_check=False)
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return

    def is_available(self):
        return self.get_ammo()[0] > 0
