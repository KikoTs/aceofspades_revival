from prefabTool import PrefabTool
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings

class ZombiePrefabTool(PrefabTool):
    name = strings.PREFAB_TOOL
    model = [ZOMBIE_HAND_MODEL, BLOCK_MODEL, ZOMBIE_HAND_LEFT_MODEL]
    view_model = [ZOMBIE_HAND_VIEW_MODEL, BLOCK_VIEW_MODEL]

    def __init__(self, character):
        super(ZombiePrefabTool, self).__init__(character)
        if self.character.main:
            self.initial_orientation[0] = Vector3(0.0, 0.0, 180.0)
            self.reset_orientation(0)
            self.initial_orientation[1] = Vector3(0.0, 45.0, 30.0)
            self.reset_orientation(1)
            self.initial_position[0] = Vector3(0.0, 0.0, 0.0)
            self.reset_position(0)
            self.initial_position[1] = Vector3(0.0, 0.2, 0.8)
            self.reset_position(1)

    def needs_player_arms_drawing(self):
        return False
