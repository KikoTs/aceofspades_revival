from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from pyglet.gl import *
from aoslib.shaders import *
from aoslib.draw import DisplayList
from shared.glm import Vector3
from aoslib import strings, media
from tool import Tool
from aoslib import media
from aoslib import strings
from aoslib.animations.animPlaceBlock import *
ghost_medpack = DisplayList(MEDPACK_VIEW_MODEL)
ghost_medpack.size = 0.06

class MedPackWeapon(Weapon):
    name = strings.MEDPACK_WEAPON
    damage = None
    sight = None
    shoot_sound = None
    reload_time = A1860
    clip_reload = False
    shoot_interval = A1865
    model = [MEDPACK_MODEL]
    view_model = [MEDPACK_VIEW_MODEL]
    model_size = 0.04
    view_model_size = 0.07
    image = TOOL_IMAGES[MEDPACK_TOOL]
    noof_primary_blocks = 1
    ammo = (A1868, A1869, None, None, A1870)
    ghost_position = None

    def __init__(self, character):
        super(MedPackWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.1, -0.18, 0.45)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, 0.1, -0.2)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)

    def shoot(self, fp3, seed):
        if not self.character.main:
            return
        if not self.ghost_position:
            self.play_sound(BUILD_ERROR_SOUND)
            return False
        character = self.character
        scene = self.character.scene
        scene.send_place_medpack(self.ghost_position, self.ghost_face)
        self.animations['place_block'].start()
        return True

    def update(self, dt):
        return super(MedPackWeapon, self).update(dt)

    def draw_ghosting(self):
        self.ghost_position = None
        can_place, ret = self.character.scene.can_place_object(self.character, A1880, player_min_radius=0, entity_min_radius=1, others_min_radius=0, can_place_vertical=False)
        if not can_place:
            return
        else:
            position, face = ret
            self.ghost_position = (
             position.x + 0.5, position.y + 0.5, position.z)
            self.ghost_face = face
            o, ox, oy, oz = (0, 0, 0, 0)
            glPushMatrix()
            glTranslatef(self.ghost_position[0], -self.ghost_position[2], self.ghost_position[1])
            glRotatef(o, ox, oy, oz)
            glTranslatef(0, -A1875, 0)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 0.3)
            ghost_medpack.draw(frustum_check=False)
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return

    def on_set(self):
        Weapon.on_set(self)
        self.current_ammo = self.get_ammo()[0]

    def on_unset(self):
        Weapon.on_unset(self)
