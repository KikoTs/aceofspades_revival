from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUsePickAxe import *
from aoslib import strings

class PickAxeTool(DiggingTool):
    name = strings.PICKAXE
    model = [PICKAXE_MODEL]
    view_model = [PICKAXE_VIEW_MODEL]
    image = TOOL_IMAGES[PICKAXE_TOOL]
    shoot_interval = PICKAXE_SHOOT_INTERVAL
    damage = PICKAXE_DAMAGE_AMOUNT
    damage_type = PICKAXE_DAMAGE
    hit_player_sound = PICKAXE_HIT_PLAYER_SOUND
    hit_block_sound = PICKAXE_HIT_BLOCK_SOUND
    pitch_increase = 30

    def __init__(self, character):
        super(PickAxeTool, self).__init__(character)
        self.animations['use_pickaxe'] = AnimUsePickAxe(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MELEE)

    def use_primary(self):
        super(PickAxeTool, self).use_primary()
        self.animations['use_pickaxe'].start()
        return self.use_spade(False)
