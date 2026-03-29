from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from aoslib.draw import DisplayList
from aoslib import strings
from shared.glm import Vector3
from pyglet.gl import *
from laserAttachment import LaserAttachment

class Sniper2Weapon(Weapon):
    name = strings.SNIPER2_RIFLE
    damage = (A1375, A1376, A1377, A1378, A1378)
    block_damage = A1380
    range = A1367
    shoot_sound = SNIPER2_SHOOT_SOUND
    reload_sound = 'semi_weak_reload'
    shoot_interval = A1370
    reload_time = A1368
    accuracy = A1371
    accuracy_zoom = A1372
    recoil_up = A1373
    recoil_side = A1374
    ammo = (A1384, A1384, A1381, A1382, A1383)
    clip_reload = False
    short_ranged_distance = None
    model = [SNIPER2_MODEL]
    view_model = [SNIPER2_VIEW_MODEL]
    sight = SNIPER2_SIGHT
    casing = SNIPER2_CASING
    tracer = None
    image = TOOL_IMAGES[SNIPER2_TOOL]
    sight_pos = (0.0, 0.325, -1.85)
    muzzle_flash_display = DisplayList(MUZZLE_FLASH_SNIPER)
    muzzle_flash_view_display = DisplayList(MUZZLE_FLASH_SNIPER_VIEW)
    muzzle_flash_offset = Vector3(-12.0, 78.0, -5.0)
    muzzle_flash_view_offset = Vector3(0.0, 0.12, 0.9)
    zoom = A1385
    zoomed_sensitivity_factor = A1386

    def __init__(self, character):
        super(Sniper2Weapon, self).__init__(character)
        for model_index in range(len(self.view_model)):
            self.zoom_position_offset[model_index] = Vector3(0.325, 0.25, 0.0)
            if character.main:
                self.initial_position[model_index] = Vector3(0.0, 0.2, 0.1)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.2, -0.1)
        if character.scene and character.scene.manager and character.scene.manager.enable_sniper_beam:
            self.laser_attachment = LaserAttachment(self)
        else:
            self.laser_attachment = None
        return

    def update(self, dt):
        super(Sniper2Weapon, self).update(dt)
        if self.laser_attachment is not None:
            self.laser_attachment.update()
        return

    def draw(self, weapon_display, frustum_check=True):
        super(Sniper2Weapon, self).draw(weapon_display)
        glPopMatrix()
        if self.laser_attachment is not None:
            self.laser_attachment.draw(weapon_display, frustum_check=frustum_check)
        glPushMatrix()
        return

    def needs_zoom_arms_offset(self):
        return True
