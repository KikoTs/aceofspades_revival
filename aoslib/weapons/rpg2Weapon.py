from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings
from aoslib import media

class RPG2Weapon(Weapon):
    name = strings.ROCKET_PROPELLED_GRENADE2
    damage = None
    sight = None
    shoot_sound = RPG2_SHOOT_SOUND
    reload_sound = 'rocket_trip_reload'
    reload_done_sound = None
    accuracy = A1412
    recoil_up = A1413
    recoil_side = A1414
    reload_time = A1410
    clip_reload = True
    shoot_interval = A1415
    model = [RPG2_MODEL]
    view_model = [RPG2_VIEW_MODEL]
    sight = RPG2_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    ammo = (A1419, A1419, A1416, A1417, A1418)
    image = TOOL_IMAGES[RPG2_TOOL]

    def __init__(self, character):
        super(RPG2Weapon, self).__init__(character)
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.1, 0.0)
                self.reset_position(model_index)

        else:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = Vector3(0.0, 0.3, 0.0)
                self.reset_position(model_index)

        self.arms_position_offset = self.initial_position[0] * -1

    def shoot(self, fp3, seed):
        if self.play_shoot_sound:
            self.play_sound(self.shoot_sound, zone=media.IN_WORLD_AUDIO_ZONE)
        character = self.character
        if not character.main:
            return
        scene = character.scene
        player = character.world_object
        from aoslib.scenes.main.rocket2 import Rocket2
        x, y, z = player.position.get()
        scene.send_rocket2(player.position, fp3 * A1420)
        return True
