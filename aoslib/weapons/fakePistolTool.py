from tool import Tool
from aoslib.models import *
from . import TOOL_IMAGES
from shared.constants import *
from shared.glm import Vector3
from aoslib import image, strings

class FakePistolTool(Tool):
    name = ''
    model = [PISTOL_MODEL]
    view_model = [PISTOL_VIEW_MODEL]
    shoot_interval = 0.0
    pitch = 1.0
    image = None
    show_crosshair = NEVER_CROSSHAIR
    draw_ammo = False

    def __init__(self, character):
        super(FakePistolTool, self).__init__(character)
        self.arms_position_offset = Vector3(0.0, 0.0, 0.0)
        self.equipped_tool_tip_text = None
        return
