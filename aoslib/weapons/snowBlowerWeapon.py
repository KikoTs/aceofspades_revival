from weapon import Weapon
from . import TOOL_IMAGES
from aoslib.models import *
from shared.constants import *
from shared.glm import Vector3
from aoslib import strings, media
from tool import Tool
from aoslib import media

class SnowBlowerWeapon(Weapon):
    name = strings.ROCKET_PROPELLED_GRENADE
    damage = None
    sight = None
    shoot_sound = SNOWBLOWER_SHOOT_SOUND
    reload_sound = 'snowcan_reload'
    reload_done_sound = 'cock'
    accuracy = A1455
    recoil_up = A1456
    recoil_side = A1457
    reload_time = A1453
    clip_reload = False
    shoot_interval = A1458
    model = [SNOWBLOWER_MODEL]
    view_model = [SNOWBLOWER_VIEW_MODEL]
    sight = SNOWBLOWER_SIGHT
    sight_pos = (0.0, 0.325, -1.85)
    tracer = None
    image = TOOL_IMAGES[SNOWBLOWER_TOOL]
    noof_primary_blocks = 1
    engine_sound = None

    def __init__(self, character):
        super(SnowBlowerWeapon, self).__init__(character)
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
        x, y, z = player.position.get()
        scene.send_snowball(player.position, fp3 * A1461)
        return True

    def update(self, dt):
        if self.engine_sound:
            pos = self.get_audio_pos()
            if pos:
                self.engine_sound.set_position(*pos)
        return super(SnowBlowerWeapon, self).update(dt)

    def on_set(self):
        Weapon.on_set(self)
        if self.character.main:
            self.character.scene.hud.palette.active = self.character.scene.manager.enable_colour_palette
        self.current_ammo = self.get_ammo()[0]
        if not self.engine_sound:
            self.engine_sound = self.play_sound('snowcan_eng_lp', position=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)

    def on_unset(self):
        Weapon.on_unset(self)
        if self.character.main:
            self.character.scene.hud.palette.active = False
        if self.engine_sound:
            self.engine_sound.close()
            self.engine_sound = None
        return

    def use_an_ammo(self):
        self.character.block_count -= 1
        self.current_ammo = self.character.block_count

    def get_ammo(self):
        return (
         self.character.block_count, None)

    def get_has_enough_ammo(self):
        player = self.character.parent
        return self.character.block_count >= self.noof_primary_blocks or player and player.team and player.team.infinite_blocks

    def is_reloadable(self):
        return False

    def restock(self, type=None):
        self.current_ammo = self.get_ammo()[0]
        self.update_ammo()

    def use_custom(self):
        character = self.character
        if not character.scene.manager.enable_colour_picker:
            return False
        else:
            character.fire_secondary = False
            player = character.world_object
            max_block_distance = MAX_BLOCK_DISTANCE if not character.scene.manager.classic else CLASSIC_MAX_BLOCK_DISTANCE
            hit_scenery = character.scene.world.hitscan_accurate(player.position, player.orientation, max_block_distance)
            if hit_scenery == None:
                return False
            position, hit_block, face = hit_scenery
            if hit_block.z > Z_ABOVE_WATERPLANE:
                return False
            solid, color = character.scene.map.get_point(hit_block.x, hit_block.y, hit_block.z)
            r, g, b, a = color
            self.set_block_color((r, g, b))
            character.pullout = 0.5
            palette = character.scene.hud.palette
            if palette is not None:
                palette.hide_selection()
            return

    def set_block_color(self, color):
        self.character.set_block_color(color)
