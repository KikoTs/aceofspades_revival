from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseRiotStick import *
from aoslib import strings

class RiotStickTool(DiggingTool):
    name = strings.RIOTSTICK
    model = [RIOTSTICK_MODEL]
    view_model = [RIOTSTICK_VIEW_MODEL]
    model_size = 0.03
    view_model_size = 0.025
    image = TOOL_IMAGES[RIOTSTICK_TOOL]
    shoot_interval = A1854
    damage = A1855
    damage_type = RIOTSTICK_DAMAGE
    hit_player_sound = RIOTSTICK_HIT_PLAYER_SOUND
    hit_block_sound = RIOTSTICK_HIT_BLOCK_SOUND
    miss_sound = A2950
    pitch_increase = 50

    def __init__(self, character):
        super(RiotStickTool, self).__init__(character)
        self.arms_position_offset = Vector3(0.0, 0.03, -0.05)
        self.animations['use_riotstick'] = AnimUseRiotStick(self.shoot_interval)

    def use_primary(self):
        super(RiotStickTool, self).use_primary()
        self.animations['use_riotstick'].start()
        return self.use_spade(False)
