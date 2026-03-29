from shared.constants import *
from shared.common import distance_vector_3d, to_pitch_yaw, get_distance_from_line, get_distance_from_line_section, clamp
from aoslib.common import to_rotation_vector
from aoslib.draw import Billboard
from aoslib.shaders import SKYDOME_SHADER, SKYDOME_SHADER_TEX_LOC, SKYDOME_SHADER_TIME_LOC, SKYDOME_SHADER_UVSPEED_LOC
from pyglet.gl import *
from aoslib.weapons import hitscan_player
from aoslib import image
from shared.glm import Vector3
import math

def draw_laser_quad_vertex(x, y, z, r, g, b, a):
    glColor4ub(r, g, b, a)
    glVertex3f(x, y, z)


def draw_laser_quad(color, start_alpha=255, end_alpha=255, scale=(1.0, 1.0, 1.0), timer=0.0, uv_scroll_speed=(0.0, 0.0), tiling=(10.0, 1.0)):
    halfScale = (
     scale[0] * 0.5, scale[1] * 0.5, scale[2] * 0.5)
    glTranslatef(halfScale[0], -halfScale[2], halfScale[1])
    SKYDOME_SHADER.bind()
    SKYDOME_SHADER.uniformi_loc(SKYDOME_SHADER_TEX_LOC, 0)
    SKYDOME_SHADER.uniformf_loc(SKYDOME_SHADER_TIME_LOC, timer)
    SKYDOME_SHADER.uniformf_loc(SKYDOME_SHADER_UVSPEED_LOC, uv_scroll_speed[0], uv_scroll_speed[1])
    r, g, b = color
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    draw_laser_quad_vertex(-halfScale[0], 0.0, -halfScale[1], r, g, b, start_alpha)
    glTexCoord2f(1.0, 0.0)
    draw_laser_quad_vertex(-halfScale[0], 0.0, halfScale[1], r, g, b, end_alpha)
    glTexCoord2f(1.0, 1.0)
    draw_laser_quad_vertex(halfScale[0], 0.0, halfScale[1], r, g, b, end_alpha)
    glTexCoord2f(0.0, 1.0)
    draw_laser_quad_vertex(halfScale[0], 0.0, -halfScale[1], r, g, b, start_alpha)
    glTexCoord2f(0.0, 0.0)
    draw_laser_quad_vertex(0.0, -halfScale[2], -halfScale[1], r, g, b, start_alpha)
    glTexCoord2f(0.0, 1.0)
    draw_laser_quad_vertex(0.0, halfScale[2], -halfScale[1], r, g, b, start_alpha)
    glTexCoord2f(1.0, 1.0)
    draw_laser_quad_vertex(0.0, halfScale[2], halfScale[1], r, g, b, end_alpha)
    glTexCoord2f(1.0, 0.0)
    draw_laser_quad_vertex(0.0, -halfScale[2], halfScale[1], r, g, b, end_alpha)
    glEnd()
    SKYDOME_SHADER.unbind()


class LaserAttachment(object):
    range = 1
    scene = None
    world = None
    character = None
    hit_distance = 1
    fade_in_distance = A1358
    fade_out_distance = A1359
    start_distance = A1357
    thickness = A1360
    cube_translate_revert_x = -(thickness[0] * 0.5)
    cube_translate_revert_y = thickness[1] * 0.5
    billboard = None
    laser_dot_texture = None
    laser_texture = None
    color = (255, 255, 255)
    uv_timer = 0

    def __init__(self, owner):
        self.scene = owner.character.scene
        self.world = self.scene.world
        self.range = owner.range
        self.character = owner.character
        player = self.character.parent
        laser_spot_tex_name = 'laser_spot'
        laser_tex_name = 'laser_sight_beam_small'
        if player.get_team_id() == TEAM1:
            laser_spot_tex_name = 'laser_spot_blue'
            laser_tex_name = 'laser_sight_beam_blue'
        elif player.get_team_id() == TEAM2:
            laser_spot_tex_name = 'laser_spot_green'
            laser_tex_name = 'laser_sight_beam_green'
        self.laser_dot_texture = image.load_texture(name=laser_spot_tex_name, center=True, none_resource=True, add_path=True)
        self.laser_texture = image.load_texture(name=laser_tex_name, center=True, none_resource=True, add_path=True)
        self.alpha = 0
        self.billboard = Billboard()
        self.billboard.set_texture(self.laser_dot_texture)
        self.billboard.set_animation_vars()
        self.billboard.recreate()

    def __del__(self):
        if self.billboard:
            self.billboard.free()

    def draw_and_test_quad(self, test_distance, quad_start, hit_distance_test, quad_start_alpha, quad_end_alpha, quad_color, quad_tiling_distance=1.0, quad_scroll_speed=(1.0, 1.0)):
        quad_laser_distance = quad_start
        if self.hit_distance > test_distance:
            if self.hit_distance < hit_distance_test:
                quad_laser_distance = self.hit_distance - test_distance
            tiling_amount = quad_laser_distance / quad_tiling_distance
            draw_laser_quad(color=quad_color, start_alpha=quad_start_alpha, end_alpha=quad_end_alpha, scale=(
             self.thickness[0], quad_laser_distance, self.thickness[1]), timer=self.uv_timer, uv_scroll_speed=quad_scroll_speed, tiling=(
             A1361 * tiling_amount, 1.0))
        return quad_laser_distance

    def calculate_bank_angle(self):
        char_position = self.character.world_object.position
        camera = self.scene.camera_manager.get_camera()
        x, y, z = camera.get_position()
        fps_camera = Vector3(x, y, z)
        if self.scene.camera_manager.active_controller is None:
            if self.scene.character:
                fps_camera = self.scene.character.world_object.position
        dir_vector = char_position - fps_camera
        dir_vector.z = 0.0
        dir_vector_norm = dir_vector.norm()
        char_ori = self.character.world_object.orientation.copy()
        char_ori.z = 0.0
        char_ori_norm = char_ori.norm()
        dot_p = dir_vector_norm.dot(char_ori_norm)
        dot_p = max(min(dot_p, 1.0), -1.0)
        angle = math.acos(dot_p)
        bank = math.degrees(angle)
        p0 = char_position.copy()
        p0.z = 0.0
        p1 = p0 + char_ori * 10.0
        p1.z = 0.0
        p2 = fps_camera.copy()
        p2.z = 0.0
        det_triangle = (p1.x - p0.x) * (p2.y - p0.y) - (p2.x - p0.x) * (p1.y - p0.y)
        if det_triangle > 0.0:
            bank = 360 - bank
        return bank

    def update(self):
        character = self.character
        if character.zoom:
            self.uv_timer += 0.1
            character = self.character
            position = character.world_object.position
            orientation = character.world_object.orientation
            if not self.character.main:
                yaw_interp = self.character.yaw_interpolation
                pitch_interp = self.character.pitch_interpolation
                x, y, z = to_rotation_vector(pitch_interp, yaw_interp)
                orientation = Vector3(x, y, z)
            hit_position = None
            dot_closeness = 0.01
            scenery_hit = self.world.hitscan_accurate(position, orientation)
            if scenery_hit:
                hit_position, hit_block, face = scenery_hit
                self.hit_distance = distance_vector_3d(position, hit_position)
            else:
                self.hit_distance = self.range
                hit_position = position + orientation * self.hit_distance
            main_distance_from_line_sq = float('+inf')
            if self.scene.character is not None and self.scene.character.main and self.scene.character is not self.character:
                main_character = self.scene.character
                main_distance_from_line_sq = get_distance_from_line_section(position, hit_position, main_character.world_object.position)
            min_distance_sq = pow(A1365, 2)
            max_distance_sq = pow(A1366, 2)
            clamped = clamp(main_distance_from_line_sq, min_distance_sq, max_distance_sq)
            delta = (clamped - min_distance_sq) / (max_distance_sq - min_distance_sq)
            self.alpha = int((1 - delta) * 255)
            for player in self.scene.players.values():
                other = player.character
                if not other:
                    continue
                if other is not self.character:
                    radius = 3.0
                    distance_from_line_sq = get_distance_from_line(position, orientation, other.world_object.position)
                    if distance_from_line_sq > radius * radius:
                        continue
                    other_hit = hitscan_player(position, orientation, other)
                    other_hit_body, hit_position = other_hit
                    if other_hit and hit_position:
                        player_hit_distance = distance_vector_3d(position, hit_position)
                        if player_hit_distance < self.hit_distance:
                            self.hit_distance = player_hit_distance
                            scenery_hit = None
                        break

            if hit_position and not scenery_hit:
                self.hit_distance -= dot_closeness
                dot_position = position + orientation * self.hit_distance
                distance_lerp_value = 1.0 - self.hit_distance / self.range
                dot_size = A1363 + distance_lerp_value * (A1362 - A1363)
                dot_size = max(min(dot_size, A1362), A1363)
                if not self.character.main:
                    dot_size = A1364
                self.billboard.set_variables(dot_position.x - 0.5, dot_position.y - 0.5, dot_position.z - 0.5, dot_size, (255,
                                                                                                                          255,
                                                                                                                          255,
                                                                                                                          255), 0.0)
        return

    def draw(self, weapon_display, frustum_check=True):
        if self.character.zoom:
            glDepthMask(GL_FALSE)
            glDisable(GL_CULL_FACE)
            glActiveTexture(GL_TEXTURE0)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.laser_texture.id)
            glPushMatrix()
            glTranslatef(0.0, 0.0, 0)
            glRotatef(weapon_display.yaw, 0.0, 1.0, 0.0)
            glRotatef(weapon_display.pitch, 1.0, 0.0, 0.0)
            bank_angle = self.calculate_bank_angle()
            glRotatef(bank_angle, 0.0, 0.0, 1.0)
            glTranslatef(-(self.thickness[0] * 0.5), self.thickness[1] * 0.5, self.start_distance)
            fade_in_laser_distance = self.draw_and_test_quad(test_distance=self.start_distance, quad_start=self.fade_in_distance, hit_distance_test=self.start_distance + self.fade_in_distance, quad_start_alpha=0, quad_end_alpha=self.alpha, quad_color=self.color, quad_tiling_distance=self.fade_in_distance, quad_scroll_speed=(-0.05,
                                                                                                                                                                                                                                                                                                                                      0.0))
            glPushMatrix()
            cube_translate_revert_z = fade_in_laser_distance * 0.5
            glTranslatef(self.cube_translate_revert_x, self.cube_translate_revert_y, cube_translate_revert_z)
            opaque_laser_distance = self.range - (self.fade_out_distance + self.fade_in_distance + self.start_distance)
            second_laser_cube_test_value = self.start_distance + self.fade_in_distance
            opaque_laser_distance = self.draw_and_test_quad(test_distance=second_laser_cube_test_value, quad_start=opaque_laser_distance, hit_distance_test=opaque_laser_distance, quad_start_alpha=self.alpha, quad_end_alpha=self.alpha, quad_color=self.color, quad_tiling_distance=fade_in_laser_distance, quad_scroll_speed=(-0.0001,
                                                                                                                                                                                                                                                                                                                                  0.0))
            glPushMatrix()
            cube_translate_revert_z = opaque_laser_distance * 0.5
            glTranslatef(self.cube_translate_revert_x, self.cube_translate_revert_y, cube_translate_revert_z)
            third_laser_cube_distance_test_value = self.start_distance + self.fade_in_distance + opaque_laser_distance
            self.draw_and_test_quad(test_distance=third_laser_cube_distance_test_value, quad_start=self.fade_out_distance, hit_distance_test=self.fade_out_distance, quad_start_alpha=self.alpha, quad_end_alpha=0, quad_color=self.color, quad_tiling_distance=fade_in_laser_distance)
            glPopMatrix()
            glPopMatrix()
            glPopMatrix()
            glBindTexture(GL_TEXTURE_2D, 0)
            glActiveTexture(GL_TEXTURE0)
            glDisable(GL_TEXTURE_2D)
            glEnable(GL_CULL_FACE)
            glDepthMask(GL_TRUE)
