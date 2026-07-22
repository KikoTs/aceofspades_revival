from tool import Tool
from . import TOOL_IMAGES
from aoslib.draw import draw_cube
from aoslib.kv6 import set_kv6_default_color
from aoslib.models import *
from aoslib import *
from aoslib.world import get_next_cube, cube_line
from aoslib.draw import DisplayList
from aoslib.shaders import *
from pyglet.gl import *
from shared.constants import *
from shared.hud_constants import BIG_TEXT_TIME_1FRAME
from shared.common import get_facing, rotate_z_axis, rotate_x_axis, rotate_y_axis, clamp
from aoslib import media, strings
from aoslib.common import to_float_color
import math
from aoslib.animations.animPlaceBlock import *
from aoslib.weapons.prefabTool import PrefabTool
UGCPREFAB_INPUT_REPEAT = [
 0.0, 0.5, 0.1, 0.05]
UGCPREFAB_INPUT_ERASE_DELAY = 0.1
UGCPREFAB_BLOCK_COUNT_RELATIVE_SHOOT_DELAY_MULTIPLIER = 5e-05
UGCPREFAB_BLOCK_MAX_DELAY = 3.0
COLOR_ANIMATION_MIN = 0.9
COLOR_ANIMATION_MAX = 2.0

class UGCPrefabTool(PrefabTool):
    use_color = False
    model = [UGCPREFAB_TOOL_MODEL]
    view_model = [UGCPREFAB_TOOL_VIEW_MODEL]
    view_model_size = 0.04
    can_shoot_primary_while_sprinting = True
    can_shoot_secondary_while_sprinting = True
    never_pullout = True
    prefab_position = None
    prefab_center_position = None
    controlling_prefab = False
    color_animation = COLOR_ANIMATION_MIN
    color_animation_delta = 0.5
    input_forward = False
    input_backward = False
    input_left = False
    input_right = False
    input_up = False
    input_down = False
    input_carve = False
    input_sprint = False
    input_rotate_prefab_left = False
    input_rotate_prefab_right = False
    input_rotate_prefab_up = False
    input_rotate_prefab_down = False
    shoot_interval = 0.1
    repeat_input = [
     0, 0.0]
    zoom_level = 0
    erase_timer = 0.0

    def __init__(self, character):
        super(PrefabTool, self).__init__(character)
        self.ammo_image = TOOL_IMAGES[BLOCK_TOOL]
        self.arms_position_offset = Vector3(0.04, 0.0, -0.3)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = self.arms_position_offset * -1
                self.initial_orientation[model_index] = Vector3(0.0, 0.0, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.animations['place_block'] = AnimPlaceBlock(self.shoot_interval)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_PREFAB_TOOL)
        self.deactivate_timer = 0

    def set_sprint(self, value):
        self.input_sprint = value

    def set_walk(self, up=None, down=None, left=None, right=None):
        if self.controlling_prefab and self.prefab_position:
            if up != None:
                self.input_forward = up
            if down != None:
                self.input_backward = down
            if left != None:
                self.input_left = left
            if right != None:
                self.input_right = right
        return

    def set_jump(self, value):
        if self.controlling_prefab and self.prefab_position:
            self.input_up = value

    def set_crouch(self, value):
        if self.controlling_prefab and self.prefab_position:
            self.input_down = value

    def set_carve_prefab(self, value):
        self.input_carve = value

    def set_input_rotate_prefab_left(self, value):
        self.input_rotate_prefab_left = value

    def set_input_rotate_prefab_right(self, value):
        self.input_rotate_prefab_right = value

    def set_input_rotate_prefab_up(self, value):
        self.input_rotate_prefab_up = value

    def set_input_rotate_prefab_down(self, value):
        self.input_rotate_prefab_down = value

    def cancel_prefab_placement(self):
        if self.controlling_prefab:
            self.deactivate_control_mode()

    def apply_prefab_rotation(self, camera_relative_yaw):
        if self.input_rotate_prefab_left and not self.input_rotate_prefab_right:
            if camera_relative_yaw == NORTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
            elif camera_relative_yaw == EAST:
                if self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
            elif camera_relative_yaw == SOUTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
            elif camera_relative_yaw == WEST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
        if self.input_rotate_prefab_right and not self.input_rotate_prefab_left:
            if camera_relative_yaw == NORTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
            elif camera_relative_yaw == EAST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
            elif camera_relative_yaw == SOUTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
            elif camera_relative_yaw == WEST:
                if self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
        if self.input_rotate_prefab_up and not self.input_rotate_prefab_down:
            if camera_relative_yaw == NORTH:
                if self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
            elif camera_relative_yaw == EAST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)
            elif camera_relative_yaw == SOUTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
            elif camera_relative_yaw == WEST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
        if self.input_rotate_prefab_down and not self.input_rotate_prefab_up:
            if camera_relative_yaw == NORTH:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
            elif camera_relative_yaw == EAST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
            elif camera_relative_yaw == SOUTH:
                if self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=2, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=2)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
            elif camera_relative_yaw == WEST:
                if self.prefab_pitch == 3:
                    self.rotate_prefab(z_axis=0, x_axis=1, y_axis=0)
                    self.rotate_prefab(z_axis=1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                elif self.prefab_pitch == 1:
                    self.rotate_prefab(z_axis=0, x_axis=-1, y_axis=0)
                    self.rotate_prefab(z_axis=-1, x_axis=0, y_axis=0)
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=-1)
                else:
                    self.rotate_prefab(z_axis=0, x_axis=0, y_axis=1)

    def apply_input(self, dt):
        if self.erase_timer > 0.0:
            self.erase_timer = max(self.erase_timer - dt, 0.0)
        if self.erase_timer == 0 and self.input_carve:
            self.erase_timer = UGCPREFAB_INPUT_ERASE_DELAY
            self.erase_prefab()
        if self.prefab_position:
            if not self.input_forward and not self.input_backward and not self.input_left and not self.input_right and not self.input_up and not self.input_down and not self.input_rotate_prefab_left and not self.input_rotate_prefab_right and not self.input_rotate_prefab_up and not self.input_rotate_prefab_down:
                self.repeat_input = [
                 0, 0.0]
            else:
                self.repeat_input[1] -= dt
                if self.repeat_input[1] <= 0:
                    repeat_index = min(self.repeat_input[0] + 1, len(UGCPREFAB_INPUT_REPEAT) - 1)
                    self.repeat_input = [repeat_index, UGCPREFAB_INPUT_REPEAT[repeat_index]]
                    camera_forward = self.character.get_camera_forward()
                    camera_flat_forward = Vector3(camera_forward.x, camera_forward.y, 0.0).norm()
                    camera_left = Vector3(0, 0, 1).cross(camera_forward)
                    if abs(camera_flat_forward.x) > abs(camera_flat_forward.y):
                        if camera_flat_forward.x > 0:
                            camera_direction = EAST
                        else:
                            camera_direction = WEST
                    elif camera_flat_forward.y < 0:
                        camera_direction = NORTH
                    else:
                        camera_direction = SOUTH
                    camera_relative_yaw = (self.prefab_yaw + camera_direction) % 4
                    self.apply_prefab_rotation(camera_relative_yaw)
                    if self.controlling_prefab:
                        movement_x = 0
                        movement_y = 0
                        movement_z = 0
                        if self.input_forward:
                            movement_y += 1.0
                        if self.input_backward:
                            movement_y -= 1.0
                        if self.input_right:
                            movement_x += 1.0
                        if self.input_left:
                            movement_x -= 1.0
                        movement_vector = camera_flat_forward * movement_y + camera_left * movement_x
                        if self.input_up:
                            movement_vector.z -= 1
                        if self.input_down:
                            movement_vector.z += 1
                        if abs(movement_vector.x) > abs(movement_vector.y) and abs(movement_vector.x) > abs(movement_vector.z):
                            movement_vector.x = math.copysign(1, movement_vector.x)
                            movement_vector.y = 0
                            movement_vector.z = 0
                        elif abs(movement_vector.y) > abs(movement_vector.x) and abs(movement_vector.y) > abs(movement_vector.z):
                            movement_vector.x = 0
                            movement_vector.y = math.copysign(1, movement_vector.y)
                            movement_vector.z = 0
                        elif movement_vector.z != 0:
                            movement_vector.x = 0
                            movement_vector.y = 0
                            movement_vector.z = math.copysign(1, movement_vector.z)
                        if self.input_sprint:
                            movement_vector = movement_vector * PREFAB_SPRINT_SPEED
                        self.prefab_center_position = self.prefab_center_position + movement_vector
                        x, y, z = self.prefab_position
                        self.prefab_position = (x + movement_vector.x, y + movement_vector.y, z + movement_vector.z)

    def update(self, dt):
        if self.deactivate_timer > 0:
            self.deactivate_timer -= dt
        self.apply_input(dt)
        self.color_animation = clamp(self.color_animation + self.color_animation_delta * dt, COLOR_ANIMATION_MIN, COLOR_ANIMATION_MAX)
        if self.color_animation >= COLOR_ANIMATION_MAX or self.color_animation <= COLOR_ANIMATION_MIN:
            self.color_animation_delta = -self.color_animation_delta
        if self.prefab_manager and self.prefab_name and self.ghost_model:
            if not self.controlling_prefab:
                self.prefab_yaw = 0
                self.prefab_yaw = (self.prefab_yaw + self.prefab_yaw_override) % NOOF_DIRECTIONS
                self.prefab_pitch = 0
                self.prefab_pitch = (self.prefab_pitch + self.prefab_pitch_override) % NOOF_ORIENTATION_PITCHES
                self.prefab_roll = 0
                self.prefab_roll = (self.prefab_roll + self.prefab_roll_override) % NOOF_ORIENTATION_ROLLS
                _, position, prefab_center = self.character.scene.get_prefab_ghost_position(character=self.character, prefab_model=self.prefab_model, check_world_intersect=False, check_world_touch=True, check_visible=False, check_beach_layer=False, use_player_orientation=False, prefab_yaw=self.prefab_yaw, prefab_pitch=self.prefab_pitch, prefab_roll=self.prefab_roll, check_world_bounds=False)
                self.prefab_center_position = prefab_center
                self.rotate_prefab_centered(self.prefab_model, position, self.prefab_yaw, self.prefab_pitch, self.prefab_roll)
                new_position = self.rotate_prefab_centered(self.prefab_model, self.prefab_center_position, self.prefab_yaw, self.prefab_pitch, self.prefab_roll)
                self.prefab_position = (new_position.x, new_position.y, new_position.z)
            if self.prefab_position:
                self.can_place_prefab = not self.character.building_prefab and self.shoot_delay <= 0 and self.character.scene.get_prefab_touches_world(model=self.prefab_model, position_tuple=self.prefab_position, prefab_yaw=self.prefab_yaw, prefab_pitch=self.prefab_pitch, prefab_roll=self.prefab_roll)
            if self.character.middle_mouse_input:
                if self.can_place_prefab:
                    self.confirm_prefab_placement()
        return super(UGCPrefabTool, self).update(dt)

    def draw_ghosting(self):
        if not self.prefab_manager or self.prefab_name == None or self.ghost_model == None:
            return
        if not self.prefab_position:
            return
        else:
            if not self.character.scene.block_manager.is_space_to_add_blocks():
                self.character.scene.hud.add_big_messageBackGround(strings.BLOCK_PLACE_UGC_CAPACITY, duration=BIG_TEXT_TIME_1FRAME)
            prefab_x, prefab_y, prefab_z = self.prefab_position
            x = prefab_x + 0.5
            y = -prefab_z - 0.5
            z = prefab_y + 0.5
            glPushMatrix()
            shadow_pos = (
             x, y, z)
            glTranslatef(shadow_pos[0], shadow_pos[1], shadow_pos[2])
            glRotatef(90.0 * self.prefab_yaw, 0.0, 1.0, 0.0)
            glRotatef(90.0 * self.prefab_pitch, -1.0, 0.0, 0.0)
            glRotatef(90.0 * self.prefab_roll, 0.0, 0.0, -1.0)
            self.ghost_model.z_offset = -1.0
            MODEL_SHADER.bind()
            set_kv6_default_color(0.0, 0.0, 0.0)
            if self.can_place_prefab and self.get_has_enough_ammo() and self.character.scene.block_manager.is_space_to_add_blocks():
                r, g, b = (0.0, 0.0, 0.0)
                g = self.color_animation
                MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, r, g, b, 0.5)
            else:
                MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 0.0, 0.0, 0.4)
            self.ghost_model.draw(frustum_check=False)
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            MODEL_SHADER.unbind()
            glPopMatrix()
            return

    def confirm_prefab_placement(self):
        if self.character.main:
            if self.prefab_position == None or not self.can_place_prefab or not self.character.scene.is_space_to_add_blocks():
                self.play_sound(BUILD_ERROR_SOUND, force_non_positional=True)
                self.shoot_delay = self.shoot_interval
                return False
            self.character.scene.send_build_prefab(self.prefab_name, self.prefab_position, prefab_yaw=self.prefab_yaw, prefab_pitch=self.prefab_pitch, prefab_roll=self.prefab_roll, add_to_user_blocks=False)
            self.character.building_prefab = True
            self.shoot_delay = self.shoot_interval
            return True
        else:
            return

    def erase_prefab(self):
        if self.character.main:
            if self.prefab_position == None or not self.can_place_prefab:
                self.play_sound(BUILD_ERROR_SOUND, force_non_positional=True)
                return
            self.character.scene.send_erase_prefab(self.prefab_name, self.prefab_position, self.prefab_yaw, self.prefab_pitch, self.prefab_roll)
            self.character.building_prefab = True
        return

    def rotate_prefab_centered(self, prefab_model, prefab_position, prefab_yaw=0, prefab_pitch=0, prefab_roll=0):
        size_x, size_y, size_z = prefab_model.get_sizes()
        world_size_x, world_size_y, world_size_z = rotate_y_axis(size_x, size_y, size_z, prefab_roll)
        world_size_x, world_size_y, world_size_z = rotate_x_axis(world_size_x, world_size_y, world_size_z, prefab_pitch)
        world_size_x, world_size_y, world_size_z = rotate_z_axis(world_size_x, world_size_y, world_size_z, prefab_yaw)
        scan_position = prefab_position.copy()
        scan_position.x -= int(world_size_x / 2.0)
        scan_position.y -= int(world_size_y / 2.0)
        scan_position.z -= int(world_size_z / 2.0)
        even_prefab_rotation_compensation_offset = Vector3(0, 0, 0)
        if size_x & 1 == 0:
            if prefab_yaw == EAST:
                even_prefab_rotation_compensation_offset.y -= 1
            if prefab_yaw == SOUTH:
                even_prefab_rotation_compensation_offset.y -= 1
        if size_y & 1 == 0:
            if prefab_yaw == NORTH:
                even_prefab_rotation_compensation_offset.x += 1
            if prefab_yaw == EAST:
                even_prefab_rotation_compensation_offset.x += 1
        scan_position = scan_position + even_prefab_rotation_compensation_offset
        return scan_position

    def rotate_prefab(self, z_axis=1, x_axis=0, y_axis=0):
        if self.character.main:
            if self.controlling_prefab:
                if z_axis != 0:
                    self.prefab_yaw = (self.prefab_yaw + z_axis) % NOOF_DIRECTIONS
                if x_axis != 0:
                    self.prefab_pitch = (self.prefab_pitch + x_axis) % NOOF_ORIENTATION_PITCHES
                if y_axis != 0:
                    self.prefab_roll = (self.prefab_roll + y_axis) % NOOF_ORIENTATION_ROLLS
                new_position = self.rotate_prefab_centered(self.prefab_model, self.prefab_center_position, self.prefab_yaw, self.prefab_pitch, self.prefab_roll)
                self.prefab_position = (new_position.x, new_position.y, new_position.z)
            else:
                if z_axis != 0:
                    self.prefab_yaw_override = (self.prefab_yaw_override + z_axis) % NOOF_DIRECTIONS
                if x_axis != 0:
                    self.prefab_pitch_override = (self.prefab_pitch_override + x_axis) % NOOF_ORIENTATION_PITCHES
                if y_axis != 0:
                    self.prefab_roll_override = (self.prefab_roll_override + y_axis) % NOOF_ORIENTATION_ROLLS

    def activate_control_mode(self):
        if self.deactivate_timer > 0:
            return
        self.character.scene.stop_movement()
        self.character.set_jump(False)
        self.set_crouch(False)
        self.controlling_prefab = True
        self.character.activate_prefab_camera(self.control_mode_camera_exited)
        if self.character.scene:
            self.character.scene.hud.update_ugc_text()

    def deactivate_control_mode(self):
        self.clear_control_mode()
        self.character.deactivate_prefab_camera()

    def clear_control_mode(self):
        self.controlling_prefab = False
        self.input_forward = False
        self.input_backward = False
        self.input_left = False
        self.input_right = False
        self.input_up = False
        self.input_down = False
        self.input_sprint = False
        self.deactivate_timer = 0.5
        if self.character.scene:
            self.character.scene.hud.update_ugc_text()

    def control_mode_camera_exited(self):
        if self.controlling_prefab:
            self.clear_control_mode()

    def use_primary(self):
        if not self.character.main:
            return
        else:
            if self.prefab_position == None:
                return
            if self.controlling_prefab:
                if self.confirm_prefab_placement():
                    self.deactivate_control_mode()
            else:
                self.activate_control_mode()
            return

    def use_secondary(self):
        super(PrefabTool, self).use_secondary()
        if not self.character.main:
            return
        self.rotate_prefab()

    def on_unset(self):
        if self.character.main:
            self.prefab_position = None
            self.deactivate_control_mode()
            self.input_carve = False
            self.input_rotate_prefab_left = False
            self.input_rotate_prefab_right = False
            self.input_rotate_prefab_up = False
            self.input_rotate_prefab_down = False
        self.on_zoom(0)
        return

    def get_prefab_position(self):
        return self.prefab_center_position

    def get_prefab_zoom(self):
        return self.zoom_level

    def set_prefab_data(self, prefab_name, prefab_manager):
        super(UGCPrefabTool, self).set_prefab_data(prefab_name, prefab_manager)
        self.set_prefab_radius()

    def set_prefab_radius(self):
        size_x, size_y, size_z = self.prefab_model.get_sizes()
        prefab_sq_radius = (size_x * size_x + size_y * size_y + size_z * size_z) / 4.0
        prefab_radius = math.sqrt(prefab_sq_radius)
        self.prefab_radius = prefab_radius
        self.zoom_level = size_x * 1.73205080757 * 0.5

    def on_scroll(self, x, y, scroll_x, scroll_y):
        if self.controlling_prefab:
            self.zoom_level = min(max(self.zoom_level - scroll_y * self.prefab_radius * 0.1, 0), UGC_PREFAB_MAX_ZOOM)
            return True
        return False

    def use_custom(self):
        pass
