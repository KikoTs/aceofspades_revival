from aoslib.models import *
from . import TOOL_IMAGES
from shared.constants import *
from aoslib import media, strings
from blockToolCommon import BlockToolCommon
from aoslib.animations.animPlaceBlock import *
import math
BLOCK_ICON = TOOL_IMAGES[BLOCK_TOOL]

class BlockTool(BlockToolCommon):
    name = strings.BLOCK_TOOL
    model = [BLOCK_MODEL]
    view_model = [BLOCK_VIEW_MODEL]
    shoot_interval = 0.5
    pitch = 1.0
    use_color = True
    build_line = None
    image = TOOL_IMAGES[BLOCK_TOOL]
    noof_primary_blocks = 1
    show_crosshair = ALWAYS_CROSSHAIR

    def __init__(self, character):
        super(BlockTool, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.04, 0.0, 0.3)
                self.initial_orientation[model_index] = Vector3(0.0, 45.0, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.arms_position_offset = Vector3(0.04, 0.0, -0.3)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_BLOCK_TOOL)

    def use_secondary(self):
        if self.old_hit_cube != None:
            self.old_hit_cube = None
            self.on_stop_primary()
            self.character.shoot_primary = False
            self.character.shoot_primary_held = False
        return super(BlockTool, self).use_secondary()

    def on_start_primary(self):
        super(BlockTool, self).on_start_primary()
        if self.valid_placement:
            self.old_hit_cube = self.hit_cube
        else:
            self.old_hit_cube = None
        return

    def on_stop_primary(self):
        super(BlockTool, self).on_stop_primary()
        character = self.character
        if character.main:
            if not self.valid_placement or not self.hit_cube or not self.old_hit_cube or not self.get_has_enough_ammo() or not self.old_hit_cube_adjacent:
                self.play_sound(BUILD_ERROR_SOUND)
            else:
                character.scene.send_block_line(self.old_hit_cube.x, self.old_hit_cube.y, self.old_hit_cube.z, self.hit_cube.x, self.hit_cube.y, self.hit_cube.z)
            self.animations['place_block'].start()
        self.valid_placement = False
        self.hit_cube = None
        self.old_hit_cube = None
        return

    def is_available(self):
        return True

    def on_set(self):
        if self.character.main:
            self.character.scene.hud.palette.active = self.character.scene.manager.enable_colour_palette
            self.update_ammo()

    def get_block_cost(self):
        line_blocks_cost = len(self.get_block_line(False, False))
        return line_blocks_cost

    def is_placement_valid(self):
        return self.valid_placement

    def get_has_enough_ammo(self):
        player = self.character.parent
        return self.character.block_count > 0 and (self.character.block_count >= len(self.get_block_line(False, False)) or player and player.team and player.team.infinite_blocks)

    def on_unset(self):
        if self.character.main:
            self.character.scene.hud.palette.active = False
            self.hit_cube = old_hit_cube = None
            self.valid_placement = False
        super(BlockTool, self).on_unset()
        return

    def update_ammo(self):
        super(BlockTool, self).update_ammo()
