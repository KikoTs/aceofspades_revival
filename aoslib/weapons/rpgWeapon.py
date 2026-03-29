from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings
from aoslib import media

class RPGWeapon(Weapon):
    name = strings.ROCKET_PROPELLED_GRENADE
    damage = None
    sight = None
    shoot_sound = RPG_SHOOT_SOUND
    reload_sound = 'rocketreload'
    reload_done_sound = 'cock'
    accuracy = A1389
    recoil_up = A1390
    recoil_side = A1391
    reload_time = A1387
    clip_reload = False
    shoot_interval = A1392
    model = [RPG_MODEL]
    view_model = [RPG_VIEW_MODEL]
    sight = RPG_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    ammo = (A1396, A1396, A1393, A1394, A1395)
    image = TOOL_IMAGES[RPG_TOOL]

    def __init__(self, character):
        super(RPGWeapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.1, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = Vector3(0.0, -0.1, 0.0)

    def shoot(self, fp3, seed):
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        character = self.character
        if not character.main:
            return
        scene = character.scene
        player = character.world_object
        from aoslib.scenes.main.rocket import Rocket
        x, y, z = player.position.get()
        scene.send_rocket(player.position, fp3 * A1397)
        return True
