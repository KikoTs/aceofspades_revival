from rpg2Weapon import RPG2Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings
from aoslib import media
from aoslib.scenes.main.rocket2 import Rocket2

class UGCRPG2Weapon(RPG2Weapon):
    name = strings.UGC_RPG2
    damage = None
    sight = None
    shoot_sound = RPG2_SHOOT_SOUND
    reload_sound = 'rocket_trip_reload'
    reload_done_sound = None
    accuracy = A1436
    recoil_up = A1437
    recoil_side = A1438
    reload_time = A1434
    clip_reload = True
    shoot_interval = A1439
    model = [UGC_RPG2_MODEL]
    view_model = [UGC_RPG2_VIEW_MODEL]
    sight = UGC_RPG2_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    ammo = (A1443, A1443, A1440, A1441, A1442)
    image = TOOL_IMAGES[UGC_RPG2_TOOL]

    def get_has_enough_ammo(self):
        return True

    def use_an_ammo(self):
        pass

    def shoot(self, fp3, seed):
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        character = self.character
        if not character.main:
            return
        scene = character.scene
        player = character.world_object
        x, y, z = player.position.get()
        scene.send_ugc_rocket2(player.position, fp3 * A1444)
        return True
