from tool import Tool
from aoslib.models import *
from . import TOOL_IMAGES
from shared.constants import *
from shared.glm import Vector3
from aoslib import image, strings

class IntelTool(Tool):
    intel_icon = image.load('minimap_intel', center=True)
    name = strings.INTEL_TOOL
    model = [INTEL_MODEL]
    view_model = [INTEL_VIEW_MODEL]
    shoot_interval = 0.0
    pitch = 1.0
    image = TOOL_IMAGES[INTEL_TOOL]
    show_crosshair = NEVER_CROSSHAIR
    carried = False
    draw_ammo = False
    use_other_team_color = True
    can_shoot_primary_while_sprinting = True

    def __init__(self, character):
        super(IntelTool, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.18, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.18, 0.0)

    def use_primary(self):
        self.character.parent.drop_pickup(self.character.world_object.position, self.character.world_object.orientation * INTEL_THROW_SPEED, send_packet=self.character.main)
        self.carried = False

    def is_available(self):
        return self.carried

    def can_swap(self):
        return not self.carried

    def get_map_icon(self, viewer):
        return self.intel_icon
