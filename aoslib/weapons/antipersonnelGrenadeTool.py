from grenadeTool import GrenadeTool
from aoslib.models import *
from shared.constants import *
from . import TOOL_IMAGES
from aoslib import media, strings
from aoslib.animations.animThrowGrenade import *

class AntipersonnelGrenadeTool(GrenadeTool):
    name = strings.ANTIPERSONNEL_GRENADE_TOOL
    model = [ANTIPERSONNEL_GRENADE_MODEL]
    view_model = [ANTIPERSONNEL_GRENADE_VIEW_MODEL]
    shoot_interval = A1835
    fuse = A1838
    default_count = A1832
    initial_count = A1833
    restock_amount = A1834
    image = TOOL_IMAGES[ANTIPERSONNEL_GRENADE_TOOL]
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    accuracy_spread_min = A1845
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1846
    accuracy_spread_increase_per_shot = A1847
    accuracy_spread_reduction_speed = A1848
    max_fuse = A1838

    def __init__(self, character):
        super(AntipersonnelGrenadeTool, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.2, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.2, 0.0)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_GRENADE)

    def throw(self, fuse):
        if self.character and self.character.main:
            self.character.throw_antipersonnel_grenade(fuse)
