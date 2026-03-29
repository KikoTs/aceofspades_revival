from drillgunWeapon import DrillgunWeapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings
from aoslib import media

class UGCDrillgunWeapon(DrillgunWeapon):
    name = strings.DRILL_TOOL
    damage = None
    sight = None
    shoot_sound = DRILL_SHOOT_SOUND
    reload_sound = 'drillreload'
    reload_done_sound = 'cock'
    accuracy = A1517
    recoil_up = A1518
    recoil_side = A1519
    reload_time = A1515
    clip_reload = False
    shoot_interval = A1520
    model = [DRILLGUN_MODEL]
    view_model = [DRILLGUN_VIEW_MODEL]
    sight = DRILLGUN_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    ammo = (A1492, A1492, A1489, A1490, A1491)
    image = TOOL_IMAGES[DRILLGUN_TOOL]

    def shoot(self, orientation, seed):
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        character = self.character
        if not character.main:
            return
        scene = character.scene
        player = character.world_object
        from aoslib.scenes.main.drill import Drill
        x, y, z = player.position.get()
        scene.send_ugc_drill(player.position, orientation * A1525)
        return True

    def get_ammo_after_reload(self):
        return (1, 1)

    def get_has_enough_ammo(self):
        return True
