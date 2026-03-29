from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseKnife import *
from aoslib import strings

class KnifeTool(DiggingTool):
    name = strings.KNIFE
    model = [KNIFE_MODEL]
    view_model = [KNIFE_VIEW_MODEL]
    model_size = 0.03
    view_model_size = 0.025
    image = TOOL_IMAGES[KNIFE_TOOL]
    shoot_interval = KNIFE_SHOOT_INTERVAL
    damage = KNIFE_DAMAGE_AMOUNT
    damage_type = KNIFE_DAMAGE
    hit_player_sound = KNIFE_HIT_PLAYER_SOUND
    hit_block_sound = KNIFE_HIT_BLOCK_SOUND
    pitch_increase = 50

    def __init__(self, character):
        super(KnifeTool, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.05, 0.03, -0.05)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.05, -0.03, 0.05)
        self.animations['use_knife'] = AnimUseKnife(self.shoot_interval)

    def use_primary(self):
        super(KnifeTool, self).use_primary()
        self.animations['use_knife'].start()
        return self.use_spade(False)
