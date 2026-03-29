from aoslib.scenes.main.drawItem import DrawItem
from aoslib.models import *
from aoslib.world import Grenade as WorldGrenade
from aoslib.draw import DisplayList
from aoslib.shaders import *
from shared.constants import *
from aoslib.scenes.main.explodeOnImpactEntity import *

class GLGrenade(ExplodeOnImpactEntity):
    name = 'GLGrenade'
    size = 0.02
    model_position_offsets = []
    model = [GRENADE_MODEL]
    explode_sound = A2913
    water_explode_sound = A2914

    def __init__(self, scene, *arg, **kw):
        super(GLGrenade, self).__init__(scene, *arg, **kw)
