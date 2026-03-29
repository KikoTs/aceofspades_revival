from weapon import Weapon
from . import TOOL_IMAGES
from pyglet.gl import *
from aoslib.shaders import *
from aoslib.models import *
from aoslib.draw import DisplayList
from shared.constants import *
from shared.hud_constants import *
from aoslib import strings
from pyglet.gl import *
from shared.common import pitch_yaw_to_direction_vector
from aoslib.world import cube_line
from aoslib import media
from aoslib.text import get_resized_font_and_formatted_text_to_fit_boundaries
from aoslib.animations.animSlowPullout import *
import math

class MGWeapon(Weapon):
    name = strings.MOUNTED_GUN
    block_damage = A1581
    range = A1548
    shoot_sound = MG_SHOOT_SOUND
    reload_sound = 'smgreload'
    shoot_interval = A1553
    reload_time = A1550
    accuracy_min = A1555
    accuracy = accuracy_min
    accuracy_max = accuracy_min + A1557
    recoil_up = A1567
    recoil_side = A1569
    ammo = (A1586, A1586, A1583, A1584, A1585)
    clip_reload = False
    short_ranged_distance = None
    model = []
    view_model = []
    entity_model = []
    image = None
    sight_pos = (0.0, -0.2, 0.0)
    accuracy_spread_min = A1559
    accuracy_spread = accuracy_spread_min
    accuracy_spread_max = accuracy_spread_min + A1561
    accuracy_spread_increase_per_shot = A1563
    accuracy_spread_reduction_speed = A1565
    can_zoom = True
    show_crosshair = ALWAYS_CROSSHAIR
    variable_accuracy = True
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_MG)
    muzzle_flash_duration = 0.01
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_MG_VIEW)
    muzzle_flash_scale = 0.75
    muzzle_flash_offset = Vector3(-5.0, 69.0, 0.0)
    muzzle_flash_view_offset = Vector3(-0.0, 0.18, 2.0)
    muzzle_flash_zoomed_view_offset = Vector3(0.0, -0.1, 3.0)
    muzzle_flash_deployed_offset = Vector3(0.0, 2.4, 0.0)
    shooting = False
    entity_size = A1589
    deployment_time = A1546
    was_deployed_last_frame = False
    withdrawal_animation_start_from = 0.9
    withdrawal_animation_speed = 10
    deployment_draw_offset_fps = 0.0

    def __init__(self, character):
        self.damage = (
         A1571, A1573, A1575, A1577, A1577)
        super(MGWeapon, self).__init__(character)
        self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MACHINEGUN)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.18, 0.0)
                self.reset_position(model_index)
                self.reset_orientation(model_index)

        self.arms_position_offset = Vector3(0.0, -0.18, 0.0)
        self.create_entity_display()
        self.looping_fire_sound = None
        self.play_shoot_sound = True
        self.time_firing = 0.0
        self.muzzle_flash_display.size = self.entity_display[0].size * self.muzzle_flash_scale
        self.muzzle_flash_display.matrix = self.entity_display[0].matrix
        self.muzzle_flash_view_display.size = self.entity_display[0].size * self.muzzle_flash_scale
        self.muzzle_flash_view_display.matrix = self.entity_display[0].matrix
        self.animations['slow_pullout'] = AnimSlowPullout(self.deployment_time)
        return

    def create_entity_display(self):
        self.entity_display = []
        self.entity_model_position_offsets = []
        for model_index in range(len(self.entity_model)):
            self.entity_display.append(DisplayList(self.entity_model[model_index]))
            self.entity_display[model_index].size = self.entity_size
            self.entity_model_position_offsets.append(Vector3(0.0, 1.0, 0.5))
            self.entity_display[model_index].x = self.entity_model_position_offsets[model_index].x
            self.entity_display[model_index].y = self.entity_model_position_offsets[model_index].y
            self.entity_display[model_index].z = self.entity_model_position_offsets[model_index].z

    def is_deployed(self):
        return self.character and self.character.is_weapon_deployed

    def deploy(self, instant=True):
        if not self.is_deployed():
            self.character.set_weapon_deployed(False, self.character.yaw)
            self.character.world_object.velocity.set(0, 0, 0)
        if instant:
            self.deployment_complete()
        elif self.character:
            self.character.is_deploying_weapon = True
        if self.is_deployed():
            self.deployment_time = A1547
        else:
            self.deployment_time = A1546

    def can_display(self):
        return not self.is_deployed()

    def deployment_complete(self):
        self.was_deployed_last_frame = self.is_deployed()
        if not self.is_deployed():
            self.character.set_weapon_deployed(True, self.character.yaw)
            self.deployed_character_position = self.character.world_object.position.copy()
        else:
            self.character.set_weapon_deployed(False)
        self.update_properties()

    def update_properties(self):
        if not self.is_deployed():
            self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MACHINEGUN)
            self.damage = (
             A1571, A1573, A1575, A1577, A1577)
            self.block_damage = A1581
            self.range = A1548
            self.shoot_interval = A1553
            self.reload_time = A1550
            self.accuracy_min = A1555
            self.accuracy = self.accuracy_min
            self.accuracy_max = self.accuracy_min + A1557
            self.recoil_up = A1567
            self.recoil_side = A1569
            self.accuracy_spread_min = A1559
            self.accuracy_spread = self.accuracy_spread_min
            self.accuracy_spread_max = self.accuracy_spread_min + A1561
            self.accuracy_spread_increase_per_shot = A1563
            self.accuracy_spread_reduction_speed = A1565
        else:
            self.set_equipped_tool_tip_text(strings.EQUIPPED_TOOL_TIP_MACHINEGUN_DEPLOYED)
            self.damage = (
             A1572, A1574, A1576, A1578, A1578)
            self.block_damage = A1582
            self.range = A1549
            self.shoot_interval = A1554
            self.reload_time = A1551
            self.accuracy_min = A1556
            self.accuracy = self.accuracy_min
            self.accuracy_max = self.accuracy_min + A1558
            self.recoil_up = A1568
            self.recoil_side = A1570
            self.accuracy_spread_min = A1560
            self.accuracy_spread = self.accuracy_spread_min
            self.accuracy_spread_max = self.accuracy_spread_min + A1562
            self.accuracy_spread_increase_per_shot = A1564
            self.accuracy_spread_reduction_speed = A1566

    def update(self, dt):
        super(MGWeapon, self).update(dt)
        if self.was_deployed_last_frame != self.is_deployed():
            self.update_properties()
            self.was_deployed_last_frame = self.is_deployed()
        if self.check_deploying():
            self.show_crosshair = NEVER_CROSSHAIR
            self.character.set_primary_shoot(False)
            self.character.world_object.velocity.set(0, 0, 0)
            self.deployment_time -= dt
            if self.deployment_time > 0:
                if not self.is_deployed() and not self.character.is_deploying_weapon:
                    self.character.is_deploying_weapon = True
                    self.character.weapon_deployment_yaw = self.character.yaw
                    self.character.set_jump(False)
                    self.character.set_walk(False, False, False, False)
                    self.character.set_crouch(False)
                if self.character.main:
                    self.character.yaw = self.character.weapon_deployment_yaw
                    self.character.update_orientation()
                    self.entity_display[1].set_rotation(0.0, self.character.weapon_deployment_yaw, 0.0)
                self.yaw = self.character.yaw
                self.pitch = 0
            else:
                self.deployment_complete()
                self.deployment_time = A1546
                self.character.is_deploying_weapon = False
                self.character.weapon_custom = False
                self.character.shoot_secondary = False
        elif self.animations['slow_pullout'].is_playing():
            self.animations['slow_pullout'].stop()
        if self.is_deployed():
            if self.character.main:
                self.character.zoom = True
            self.deployment_time = A1547
        elif self.character.main:
            self.character.zoom = False
        self.deployment_time = A1546
        self.character.is_deploying_weapon = False
        self.show_crosshair = ALWAYS_CROSSHAIR
        if self.is_deployed():
            self.shoot_sound = BLANK_SOUND
            self.play_shoot_sound = False
            if self.character.can_shoot_primary() and self.can_fire():
                if not self.looping_fire_sound:
                    self.looping_fire_sound = self.play_sound('smg_fire_loop', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
                self.shooting = True
        else:
            self.shoot_sound = MG_SHOOT_SOUND
            self.play_shoot_sound = True
        if self.is_deployed():
            if self.shooting:
                self.time_firing += dt
            if self.time_firing >= self.shoot_interval:
                self.play_shoot_sound = False
                self.time_firing -= self.shoot_interval
                if not self.character.can_shoot_primary() or not self.can_fire():
                    self.shooting = False
                if not self.shooting:
                    if self.looping_fire_sound:
                        self.looping_fire_sound.close()
                        self.looping_fire_sound = None
                    self.play_sound('smg_fire_tail', position=self.get_audio_pos(), zone=media.IN_WORLD_AUDIO_ZONE)
                    self.time_firing = 0.0
            if self.character != None:
                if self.character.main:
                    diff_yaw = self.character.yaw - self.character.weapon_deployment_yaw
                    if diff_yaw > A1588:
                        self.character.yaw -= diff_yaw - A1588
                    elif diff_yaw < -A1588:
                        self.character.yaw -= diff_yaw + A1588
                    if self.character.pitch > A1587:
                        self.character.pitch = A1587
                    elif self.character.pitch < -A1587:
                        self.character.pitch = -A1587
                    self.character.update_orientation()
                self.entity_display[1].set_rotation(0.0, self.character.yaw, 0.0)
                self.yaw = self.character.yaw
                self.pitch = self.character.pitch
                if self.character.main and self.character.world_object:
                    if self.character.world_object.position.x != self.deployed_character_position.x or self.character.world_object.position.y != self.deployed_character_position.y or self.character.world_object.position.z != self.deployed_character_position.z:
                        self.deploy()
        return

    def draw_manned(self):
        if not self.is_deployed():
            return
        if self.character.world_object:
            glPushMatrix()
            glTranslatef(self.character.world_object.position.x, -self.character.world_object.position.z, self.character.world_object.position.y)
            glRotatef(self.character.weapon_deployment_yaw, 0.0, 1.0, 0.0)
            MODEL_SHADER.bind()
            MODEL_SHADER.uniformf_loc(MODEL_SHADER_BLEND_COLOR_LOC, 1.0, 1.0, 1.0, 1.0)
            self.entity_display[1].set_rotation(0.0, self.yaw - self.character.weapon_deployment_yaw, 0.0)
            self.deployment_draw_offset_fps = max(0.0, (A1547 - self.deployment_time) / A1547 - self.withdrawal_animation_start_from) * self.withdrawal_animation_speed
            glTranslatef(0, -self.deployment_draw_offset_fps, -self.deployment_draw_offset_fps)
            self.entity_display[1].add_rotation(self.pitch, 0.0, 0.0)
            for model_index in range(len(self.entity_model)):
                self.entity_display[model_index].draw()

            MODEL_SHADER.unbind()
            glTranslatef(self.entity_display[0].x, -self.entity_display[0].z, self.entity_display[0].y)
            glRotatef(self.yaw - self.character.weapon_deployment_yaw, 0.0, 1.0, 0.0)
            glRotatef(self.pitch, 1.0, 0.0, 0.0)
            glTranslatef(self.muzzle_flash_deployed_offset.x, -self.muzzle_flash_deployed_offset.z, self.muzzle_flash_deployed_offset.y)
            self.draw_deployed_muzzle()
            glPopMatrix()

    def on_unset(self):
        if self.character.main:
            self.character.zoom = False
        if self.looping_fire_sound:
            self.looping_fire_sound.close()
            self.looping_fire_sound = None
        self.time_firing = 0.0
        super(MGWeapon, self).on_unset()
        self.deployment_time = 0
        if self.character:
            self.character.is_deploying_weapon = False
        self.shoot_delay = 0
        if self.is_deployed():
            self.deploy()
        return

    def can_shoot_primary(self):
        if self.character.is_deploying_weapon:
            return False
        return super(MGWeapon, self).can_shoot_primary()

    def can_swap(self):
        return not self.is_deployed() and not self.character.is_deploying_weapon

    def check_deploying(self):
        if not (self.character.weapon_custom or self.character.shoot_secondary):
            return False
        if not self.is_deployed():
            if self.is_crouching():
                return False
            if not self.check_available_space_for_deployment():
                return False
        if not self.character.is_deploying_weapon:
            self.animations['slow_pullout'].start()
        return True

    def check_available_space_for_deployment(self):
        character = self.character
        if not character.world_object:
            return False
        character_position = character.world_object.position
        scene = character.scene
        map = scene.map
        yaw = character.yaw
        x, y, z = pitch_yaw_to_direction_vector(0, math.radians(yaw))
        deploy_direction = Vector3(x, y, 0).norm()
        target_pos = character_position + deploy_direction * 2
        points = cube_line(character_position.x, character_position.y, character_position.z, target_pos.x, target_pos.y, target_pos.z)
        for delta_z in xrange(0, 3):
            for point in points:
                x, y, z = point
                block = Vector3(x, y, z + delta_z)
                if map.get_solid(block.x, block.y, block.z):
                    return False

        delta_z = 3
        for point in points:
            x, y, z = point
            block = Vector3(x, y, z + delta_z)
            if not map.get_solid(block.x, block.y, block.z):
                return False

        return True

    def draw_deployed_muzzle(self):
        if self.muzzle_flash_view_display:
            if self.muzzle_flash_timer > 0:
                glRotatef(self.muzzle_flash_rotation, 0.0, 0.0, 1.0)
                PASSTHROUGH_SHADER.bind()
                self.muzzle_flash_view_display.draw()
                PASSTHROUGH_SHADER.unbind()

    def get_deployment_progress(self):
        if self.is_deployed():
            return self.deployment_time / A1547
        else:
            return self.deployment_time / A1546

    def can_reload_while_zoomed(self):
        return True
