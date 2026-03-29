from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseMachete import *
from aoslib import strings

class MacheteTool(DiggingTool):
    name = strings.MACHETE
    model = [MACHETE_MODEL]
    view_model = [MACHETE_VIEW_MODEL]
    model_size = 0.03
    view_model_size = 0.025
    image = TOOL_IMAGES[MACHETE_TOOL]
    shoot_interval = A1857
    damage = A1858
    damage_type = MACHETE_DAMAGE
    hit_player_sound = MACHETE_HIT_PLAYER_SOUND
    hit_block_sound = MACHETE_HIT_BLOCK_SOUND
    miss_sound = A2956
    pitch_increase = 50

    def __init__(self, character):
        super(MacheteTool, self).__init__(character)
        self.arms_position_offset = Vector3(0.0, 0.03, -0.05)
        self.animations['use_machete'] = AnimUseMachete(self.shoot_interval)

    def use_primary(self):
        super(MacheteTool, self).use_primary()
        self.animations['use_machete'].start()
        return self.use_spade(False)
