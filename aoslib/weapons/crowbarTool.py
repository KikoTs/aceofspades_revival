from diggingTool import DiggingTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.animations.animUseCrowbar import *
from aoslib import strings

class CrowbarTool(DiggingTool):
    name = strings.CROWBAR_TOOL
    model = [CROWBAR_MODEL]
    model_size = 1.3 * BODY_PARTS_SIZE * 0.666
    view_model = [CROWBAR_VIEW_MODEL]
    image = TOOL_IMAGES[CROWBAR_TOOL]
    shoot_interval = CROWBAR_SHOOT_INTERVAL
    damage = CROWBAR_DAMAGE_AMOUNT
    damage_type = CROWBAR_DAMAGE
    hit_player_sound = CROWBAR_HIT_PLAYER_SOUND
    hit_block_sound = CROWBAR_HIT_BLOCK_SOUND
    pitch_increase = 30

    def __init__(self, character):
        super(CrowbarTool, self).__init__(character)
        self.animations['use_crowbar'] = AnimUseCrowbar(self.shoot_interval)

    def use_primary(self):
        super(CrowbarTool, self).use_primary()
        self.animations['use_crowbar'].start()
        return self.use_spade(False)
