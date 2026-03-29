from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from pyglet.gl import *
from laserAttachment import LaserAttachment

class SniperWeapon(Weapon):
    name = strings.SNIPER_RIFLE
    damage = (A1345, A1346, A1347, A1348, A1348)
    block_damage = A1350
    range = A1337
    shoot_sound = SNIPER_SHOOT_SOUND
    reload_sound = 'semireload'
    shoot_interval = A1340
    reload_time = A1338
    accuracy = A1341
    accuracy_zoom = A1342
    recoil_up = A1343
    recoil_side = A1344
    ammo = (A1354, A1354, A1351, A1352, A1353)
    clip_reload = False
    short_ranged_distance = None
    model = [SNIPER_MODEL]
    view_model = [SNIPER_VIEW_MODEL]
    sight = SNIPER_SIGHT
    casing = SNIPER_CASING
    tracer = None
    sight_pos = (0.0, 0.325, -0.0)
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SNIPER)
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SNIPER_VIEW)
    muzzle_flash_offset = Vector3(-12.0, 78.0, -5.0)
    muzzle_flash_view_offset = Vector3(0.0, 0.12, 0.9)
    zoom = A1355
    zoomed_sensitivity_factor = A1356
    image = TOOL_IMAGES[SNIPER_TOOL][2]

    def __init__(self, character):
        super(SniperWeapon, self).__init__(character)
        for model_index in range(len(self.view_model)):
            self.zoom_position_offset[model_index] = Vector3(0.325, 0.25, 0.0)
            if character.main:
                self.initial_position[model_index] = Vector3(0.0, 0.1, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.1, 0.0)
        player = character.parent
        self.image = TOOL_IMAGES[SNIPER_TOOL][player.team.id - TEAM1]
        if character.scene and character.scene.manager and character.scene.manager.enable_sniper_beam:
            self.laser_attachment = LaserAttachment(self)
        else:
            self.laser_attachment = None
        return

    def update(self, dt):
        super(SniperWeapon, self).update(dt)
        if self.laser_attachment is not None:
            self.laser_attachment.update()
        return

    def draw(self, weapon_display, frustum_check=True):
        super(SniperWeapon, self).draw(weapon_display)
        glPopMatrix()
        if self.laser_attachment is not None:
            self.laser_attachment.draw(weapon_display, frustum_check=frustum_check)
        glPushMatrix()
        return

    def needs_zoom_arms_offset(self):
        return True
