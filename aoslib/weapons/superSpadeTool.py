from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseSpade import *
from aoslib import strings

class SuperSpadeTool(DiggingTool):
    name = strings.SUPER_SPADE
    model = [SUPERSPADE_MODEL]
    view_model = [SUPERSPADE_VIEW_MODEL]
    shoot_interval = SUPERSPADE_SHOOT_INTERVAL
    image = TOOL_IMAGES[SUPERSPADE_TOOL]
    damage = SUPERSPADE_DAMAGE_AMOUNT
    damage_type = SUPERSPADE_DAMAGE
    hit_block_sound = SUPER_SPADE_HIT_BLOCK_SOUND
    pitch_increase = 40

    def __init__(self, character):
        super(SuperSpadeTool, self).__init__(character)
        self.animations['use_spade'] = AnimUseSpade(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MELEE)

    def use_primary(self):
        super(SuperSpadeTool, self).use_primary()
        self.animations['use_spade'].start()
        return self.use_spade(False)
