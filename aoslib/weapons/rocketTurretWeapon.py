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
from aoslib.scenes.main.rocketTurret import RocketTurret

class RocketTurretWeapon(Weapon):
    name = strings.ROCKET_TURRET
    damage = None
    sight = None
    shoot_sound = None
    model = [TURRET_BASE_TOOL_MODEL, TURRET_BALL_TOOL_MODEL, TURRET_GUN_TOOL_MODEL]
    view_model = [TURRET_BASE_VIEW_MODEL, TURRET_BALL_VIEW_MODEL, TURRET_GUN_VIEW_MODEL]
    ghost_rocket_turret = [DisplayList(TURRET_BASE_TOOL_MODEL), DisplayList(TURRET_BALL_TOOL_MODEL), DisplayList(TURRET_GUN_TOOL_MODEL)]
    ghost_rocket_turret_size = 0.06
    ghost_rocket_turret_position_offsets = []
    tracer = None
    ammo = (A1600, A1601, None, None, A1602)
    shoot_interval = A1604
    ghost_position = None
    image = TOOL_IMAGES[ROCKET_TURRET_TOOL]

    def __init__(self, character):
        super(RocketTurretWeapon, self).__init__(character)
        self.arms_position_offset = Vector3(0.0, -0.18, 0.0)
        if character.main:
            self.initial_position[0] = Vector3(-15.0, 0.0, 10.0) - self.arms_position_offset
            self.initial_position[1] = Vector3(-15.0, 14.0, 10.0) - self.arms_position_offset
            self.initial_position[2] = Vector3(-15.0, 8.0, 10.0) - self.arms_position_offset
        else:
            self.initial_position[0] = Vector3(-15.0, 0.0, 10.0) - self.arms_position_offset
            self.initial_position[1] = Vector3(-15.0, 0.0, 10.0) - self.arms_position_offset
            self.initial_position[2] = Vector3(-15.0, 0.0, 10.0) - self.arms_position_offset
        self.initial_position[0] = self.initial_position[0] * 0.05
        self.initial_position[1] = self.initial_position[1] * 0.05
        self.initial_position[2] = self.initial_position[2] * 0.05
        self.reset_position(0)
        self.reset_position(1)
        self.reset_position(2)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        for display_model_index in range(len(self.ghost_rocket_turret)):
            self.ghost_rocket_turret[display_model_index].size = self.ghost_rocket_turret_size

        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_ROCKET_TURRET)

    def draw_ghosting(self):
        self.ghost_position = None
        can_place_rocket_turret, ret = self.character.scene.can_place_object(self.character, far_radius=A1603, player_min_radius=1, entity_min_radius=1, others_min_radius=0)
        if not can_place_rocket_turret:
            return
        else:
            position, face = ret
            self.ghost_position = position.get()
            glPushMatrix()
            glColor4f(1.0, 1.0, 1.0, 1.0)
            glTranslatef(position.x + 0.5, -position.z, position.y - 0.5)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 0.3)
            for display_model_index in range(len(self.ghost_rocket_turret)):
                self.ghost_rocket_turret[display_model_index].draw(frustum_check=False)

            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return

    def shoot(self, fp3, seed):
        if not self.character.main:
            return False
        if not self.ghost_position:
            return False
        self.character.scene.send_place_rocket_turret(self.ghost_position)
        self.animations['place_block'].start()
        return True

    def is_available(self):
        return self.get_ammo()[0] > 0
