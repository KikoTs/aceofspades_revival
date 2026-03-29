from tool import Tool
from aoslib.draw import draw_cube
from aoslib.kv6 import set_kv6_default_color
from aoslib.models import *
from aoslib import *
from aoslib.weapons import TOOL_IMAGES
from aoslib.world import get_next_cube, cube_line
from aoslib.draw import DisplayList
from aoslib.shaders import *
from pyglet.gl import *
from shared.constants import *
from shared.common import get_facing
from aoslib import media, strings
from aoslib.common import to_float_color
import math
from aoslib.animations.animPlaceBlock import *

class PrefabTool(Tool):
    name = strings.PREFAB_TOOL
    model = [BLOCK_MODEL]
    view_model = [BLOCK_VIEW_MODEL]
    use_color = True
    shoot_interval = 0.5
    secondary_shoot_interval = 0.5
    pitch = 1.0
    image = TOOL_IMAGES[PREFAB_TOOL]
    prefab_name = None
    prefab_manager = None
    prefab_position = (0.0, 0.0, 0.0)
    prefab_yaw = NORTH
    prefab_pitch = FORWARD_ORIENTATION_PITCH
    prefab_roll = TOP_FACES_UP_ORIENTATION_ROLL
    DEFAULT_ORIENTATION_OVERRIDE = 1
    prefab_yaw_override = DEFAULT_ORIENTATION_OVERRIDE
    prefab_pitch_override = 0
    prefab_roll_override = 0
    prefab_model = None
    prefab_cost = 0
    ghost_model = None
    prefab_cost_icon = None
    can_place_prefab = False
    show_crosshair = ALWAYS_CROSSHAIR

    def __init__(self, character):
        super(PrefabTool, self).__init__(character)
        self.ammo_image = TOOL_IMAGES[BLOCK_TOOL]
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(-0.04, 0.0, 0.3)
                self.initial_orientation[model_index] = Vector3(0.0, 45.0, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.arms_position_offset = Vector3(0.04, 0.0, -0.3)
        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_PREFAB_TOOL)

    def change_orientation(self):
        self.prefab_yaw_override = (self.prefab_yaw_override + 1) % NOOF_DIRECTIONS

    def is_placement_valid(self):
        return self.can_place_prefab and self.get_has_enough_ammo()

    def draw_ghosting(self):
        if self.prefab_manager == None or self.prefab_name == None or self.ghost_model == None:
            return
        character = self.character
        player = character.world_object
        self.prefab_yaw = get_facing(player.orientation[0], player.orientation[1])
        self.prefab_yaw = (self.prefab_yaw + self.prefab_yaw_override) % NOOF_DIRECTIONS
        self.can_place_prefab, position, prefab_center = character.scene.get_prefab_ghost_position(character=character, prefab_model=self.prefab_model, check_world_intersect=True, check_world_touch=True, check_visible=True, check_beach_layer=True, prefab_yaw=self.prefab_yaw, prefab_pitch=self.prefab_pitch, prefab_roll=self.prefab_roll, check_world_bounds=True)
        self.prefab_position = (position.x, position.y, position.z)
        x = position.x + 0.5
        y = -position.z - 0.5
        z = position.y + 0.5
        glPushMatrix()
        shadow_pos = (
         x, y, z)
        glTranslatef(shadow_pos[0], shadow_pos[1], shadow_pos[2])
        glRotatef(90.0 * self.prefab_yaw, 0.0, 1.0, 0.0)
        self.ghost_model.z_offset = -1.0
        MODEL_SHADER.bind()
        set_kv6_default_color(0.0, 0.0, 0.0)
        if self.can_place_prefab and self.get_has_enough_ammo():
            r, g, b = to_float_color(character.block_color)
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, r, g, b, 0.5)
        else:
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 0.0, 0.0, 0.4)
        self.ghost_model.draw(frustum_check=False)
        MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
        MODEL_SHADER.unbind()
        glPopMatrix()
        return

    def use_primary(self):
        super(PrefabTool, self).use_primary()
        if self.character.main:
            if self.prefab_position == None or not self.get_has_enough_ammo() or not self.can_place_prefab:
                self.play_sound(BUILD_ERROR_SOUND)
                return
            self.character.scene.send_build_prefab(self.prefab_name, self.prefab_position, prefab_yaw=self.prefab_yaw, prefab_pitch=self.prefab_pitch, prefab_roll=self.prefab_roll, add_to_user_blocks=True)
        if self.character.main:
            self.prefab_position = (0.0, 0.0, 0.0)
        self.animations['place_block'].start()
        return

    def use_secondary(self):
        self.secondary_shoot_delay = self.secondary_shoot_interval
        if self.character.main:
            self.character.weapon_object.change_orientation()
        super(PrefabTool, self).use_secondary()

    def set_prefab_data(self, prefab_name, prefab_manager):
        self.prefab_name = prefab_name
        self.prefab_yaw_override = self.DEFAULT_ORIENTATION_OVERRIDE
        self.prefab_pitch_override = 0
        self.prefab_roll_override = 0
        self.prefab_yaw = 0
        self.prefab_pitch = 0
        self.prefab_roll = 0
        if self.prefab_manager == None:
            self.prefab_manager = prefab_manager
        if self.prefab_name == None or self.prefab_manager == None:
            return
        id = self.prefab_manager.get_prefab_id_by_name(prefab_name)
        if id is None:
            return
        else:
            self.prefab_cost = self.prefab_manager.get_prefab_block_count(id)
            self.prefab_model = self.prefab_manager.prefab_palette[id]['model']
            if self.prefab_model == None:
                return
            self.ghost_model = DisplayList(self.prefab_model)
            model = self.ghost_model
            self.prefab_cost_icon = self.prefab_manager.prefab_palette[id]['image']
            return

    def get_ammo(self):
        return (
         self.character.block_count, None)

    def is_available(self):
        return True

    def get_has_enough_ammo(self):
        player = self.character.parent
        return self.character.block_count >= self.prefab_cost or player and player.team and player.team.infinite_blocks

    def on_set(self):
        if self.character.main:
            self.update_ammo()

    def on_unset(self):
        if self.character.main:
            self.prefab_name = None
            self.prefab_position = (0.0, 0.0, 0.0)
            self.ghost_model = None
            self.prefab_cost_icon = None
        super(PrefabTool, self).on_unset()
        return

    def update_ammo(self):
        Tool.update_ammo(self)

    def use_custom(self):
        character = self.character
        if not character.scene.manager.enable_colour_picker:
            return False
        else:
            if not self.prefab_position:
                return False
            character.fire_secondary = False
            player = character.world_object
            prefab_distance = player.position.distance(Vector3(*self.prefab_position))
            hit_scenery = character.scene.world.hitscan_accurate(player.position, player.orientation, prefab_distance)
            if hit_scenery is None:
                return False
            position, hit_block, face = hit_scenery
            if hit_block.z > Z_ABOVE_WATERPLANE:
                return False
            solid, color = character.scene.map.get_point(hit_block.x, hit_block.y, hit_block.z)
            r, g, b, a = color
            self.set_block_color((r, g, b))
            character.pullout = 0.5
            palette = character.scene.hud.palette
            if palette is not None:
                palette.hide_selection()
            return

    def set_block_color(self, color):
        self.character.set_block_color(color)

    def update(self, dt):
        if not self.character.shoot_secondary:
            self.secondary_shoot_delay = 0.0
        return super(PrefabTool, self).update(dt)
