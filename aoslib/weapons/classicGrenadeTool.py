from grenadeTool import GrenadeTool
from aoslib.models import *
from shared.constants import *
from . import TOOL_IMAGES
from aoslib import media, strings
from aoslib.animations.animThrowGrenade import *

class ClassicGrenadeTool(GrenadeTool):
    name = strings.CLASSIC_GRENADE
    shoot_interval = CLASSIC_GRENADE_SHOOT_INTERVAL
    fuse = CLASSIC_GRENADE_EXPLOSION_FUSE
    default_count = CLASSIC_GRENADE_STOCK
    initial_count = CLASSIC_GRENADE_INITIAL_STOCK
    restock_amount = CLASSIC_GRENADE_RESTOCK_AMOUNT
    image = TOOL_IMAGES[CLASSIC_GRENADE_TOOL]
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    accuracy_spread_min = CLASSIC_GRENADE_ACCURACY_SPREAD_INITIAL
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + CLASSIC_GRENADE_ACCURACY_SPREAD_RANGE
    accuracy_spread_increase_per_shot = CLASSIC_GRENADE_ACCURACY_SPREAD_INCREASE_PER_SHOT
    accuracy_spread_reduction_speed = CLASSIC_GRENADE_ACCURACY_SPREAD_REDUCTION_SPEED
    max_fuse = CLASSIC_GRENADE_EXPLOSION_FUSE

    def __init__(self, character):
        super(ClassicGrenadeTool, self).__init__(character)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_GRENADE)

    def throw(self, fuse):
        if self.character and self.character.main:
            self.character.throw_grenade(fuse, classic=True)
