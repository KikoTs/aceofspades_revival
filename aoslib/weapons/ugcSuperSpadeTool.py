from superSpadeTool import SuperSpadeTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib import strings

class UGCSuperSpadeTool(SuperSpadeTool):
    name = strings.UGC_SUPERSPADE
    model = [UGC_SUPERSPADE_MODEL]
    view_model = [UGC_SUPERSPADE_VIEW_MODEL]
    shoot_interval = UGC_SUPERSPADE_SHOOT_INTERVAL
    secondary_shoot_interval = UGC_SUPERSPADE_SHOOT_INTERVAL
    delay_secondary = False
    image = TOOL_IMAGES[UGC_SUPERSPADE_TOOL]
    damage = UGC_SUPERSPADE_DAMAGE_AMOUNT
    secondary_damage = UGC_SUPERSPADE_SECONDARY_DAMAGE_AMOUNT
    damage_type = UGC_SUPERSPADE_DAMAGE
    hit_block_sound = SUPER_SPADE_HIT_BLOCK_SOUND
    has_secondary = True

    def use_secondary(self):
        super(UGCSuperSpadeTool, self).use_secondary()
        self.animations['use_spade'].start()
        return self.use_spade(True)

    hit_block_sound = SUPER_SPADE_HIT_BLOCK_SOUND
