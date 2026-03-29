from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseSpade import *
from aoslib import strings

class SpadeTool(DiggingTool):
    name = strings.SPADE
    model = [SPADE_MODEL]
    view_model = [SPADE_VIEW_MODEL]
    shoot_interval = SPADE_SHOOT_INTERVAL
    secondary_shoot_interval = 1.0
    delay_secondary = True
    image = TOOL_IMAGES[SPADE_TOOL]
    damage = SPADE_DAMAGE_AMOUNT
    damage_type = SPADE_DAMAGE
    pitch_increase = 40

    def __init__(self, character):
        super(SpadeTool, self).__init__(character)
        self.animations['use_spade'] = AnimUseSpade(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MELEE)

    def use_primary(self):
        super(SpadeTool, self).use_primary()
        self.animations['use_spade'].start()
        return self.use_spade(False)
