from pickAxeTool import PickAxeTool
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib import strings

class UGCPickAxeTool(PickAxeTool):
    name = strings.UGC_PICKAXE
    model = [UGC_PICKAXE_MODEL]
    view_model = [UGC_PICKAXE_VIEW_MODEL]
    image = TOOL_IMAGES[PICKAXE_TOOL]
    shoot_interval = UGC_PICKAXE_SHOOT_INTERVAL
    damage = UGC_PICKAXE_DAMAGE_AMOUNT
    damage_type = UGC_PICKAXE_DAMAGE
    hit_player_sound = PICKAXE_HIT_PLAYER_SOUND
    hit_block_sound = PICKAXE_HIT_BLOCK_SOUND
