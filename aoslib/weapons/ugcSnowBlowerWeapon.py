from snowBlowerWeapon import SnowBlowerWeapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.hud_constants import BIG_TEXT_TIME_1FRAME
from shared.glm import Vector3
from aoslib import strings, media
from tool import Tool
from aoslib import media

class UGCSnowBlowerWeapon(SnowBlowerWeapon):
    name = strings.ROCKET_PROPELLED_GRENADE
    damage = None
    sight = None
    shoot_sound = SNOWBLOWER_SHOOT_SOUND
    reload_sound = 'snowcan_reload'
    reload_done_sound = 'cock'
    accuracy = A1470
    recoil_up = A1471
    recoil_side = A1472
    reload_time = A1468
    clip_reload = False
    shoot_interval = A1473
    model = [SNOWBLOWER_MODEL]
    view_model = [SNOWBLOWER_VIEW_MODEL]
    sight = SNOWBLOWER_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    image = TOOL_IMAGES[UGC_SNOWBLOWER_TOOL]
    noof_primary_blocks = 1
    engine_sound = None

    def shoot(self, fp3, seed):
        if not self.get_has_enough_ammo():
            return
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        character = self.character
        if not character.main:
            return
        scene = character.scene
        player = character.world_object
        x, y, z = player.position.get()
        scene.send_ugc_snowball(player.position, fp3 * A1461)
        return True

    def draw_fps(self, weapon_display):
        if not self.get_has_enough_ammo():
            self.character.scene.hud.add_big_messageBackGround(strings.BLOCK_PLACE_UGC_CAPACITY, duration=BIG_TEXT_TIME_1FRAME)
        return super(UGCSnowBlowerWeapon, self).draw_fps(weapon_display)

    def use_an_ammo(self):
        pass

    def get_has_enough_ammo(self):
        return self.character.scene.block_manager.is_space_to_add_blocks()
