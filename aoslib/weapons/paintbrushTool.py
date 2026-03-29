from tool import Tool
from aoslib.models import *
from . import TOOL_IMAGES
from shared.constants import *
from shared.constants_audio import PAINT_SECONDARY_FADE_IN_DURATION, PAINT_SECONDARY_FADE_OUT_DURATION, FADE_IN, FADE_OUT
from shared.glm import Vector3
from aoslib import image, strings, media

class PaintbrushTool(Tool):
    name = strings.PAINTBRUSH
    model = [PAINTBRUSH_TOOL_MODEL]
    view_model = [PAINTBRUSH_TOOL_VIEW_MODEL]
    shoot_interval = 0.0
    pitch = 1.0
    image = TOOL_IMAGES[PAINTBRUSH_TOOL]
    show_crosshair = ALWAYS_CROSSHAIR
    draw_ammo = False
    shoot_interval = 0.05
    use_color = True
    view_model_size = 0.03
    can_shoot_primary_while_sprinting = True
    can_shoot_secondary_while_sprinting = True
    never_pullout = True

    def __init__(self, character):
        super(PaintbrushTool, self).__init__(character)
        self.equipped_tool_tip_text = None
        self.arms_position_offset = Vector3(0, 0, -0.0)
        self.looping_paint_sound = None
        self.fade = None
        self.fade_time = 0
        if character.main:
            for model_index in range(len(self.view_model)):
                self.initial_position[model_index] = self.arms_position_offset * -1
                self.reset_position(model_index)

        return

    def on_set(self):
        super(PaintbrushTool, self).on_set()
        if self.character.main:
            self.character.scene.hud.palette.active = True
            self.update_ammo()

    def on_unset(self):
        super(PaintbrushTool, self).on_unset()
        if self.character.main:
            self.character.scene.hud.palette.active = False
        if self.looping_paint_sound is not None:
            self.looping_paint_sound.close()
            self.looping_paint_sound = None
            self.fade = None
            self.fade_time = 0
        return

    def set_block_color(self, color):
        self.character.set_block_color(color)

    def can_shoot_secondary(self):
        return self.character.scene.manager.enable_colour_picker

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

    def update(self, dt):
        if self.looping_paint_sound is not None:
            pos = self.get_audio_pos()
            if pos:
                self.looping_paint_sound.set_position(*pos)
            fade_duration = self.get_fade_duration()
            self.fade_time = min(self.fade_time + dt, fade_duration)
            if self.fade == FADE_IN:
                self.looping_paint_sound.set_volume(self.fade_time / fade_duration)
            elif self.fade == FADE_OUT:
                self.looping_paint_sound.set_volume(1.0 - self.fade_time / fade_duration)
            if self.fade_time >= fade_duration:
                if self.fade == FADE_OUT:
                    self.looping_paint_sound.close()
                    self.looping_paint_sound = None
                self.fade_time = 0
                self.fade = None
        return super(PaintbrushTool, self).update(dt)

    def use_secondary(self):
        super(PaintbrushTool, self).use_secondary()
        return True

    def on_stop_secondary(self):
        if self.looping_paint_sound is not None:
            self.fade = FADE_OUT
            self.fade_time = (1.0 - self.looping_paint_sound.get_volume()) * self.get_fade_duration()
        super(PaintbrushTool, self).on_stop_secondary()
        return

    def on_start_secondary(self):
        self.fade = FADE_IN
        if self.looping_paint_sound is None:
            self.looping_paint_sound = self.character.play_sound(name='ugc_colour_spraying', volume=0.0, pos=self.get_audio_pos(), loops=0, zone=media.IN_WORLD_AUDIO_ZONE)
            self.fade_time = 0
        else:
            self.fade_time = self.looping_paint_sound.get_volume() * self.get_fade_duration()
        super(PaintbrushTool, self).on_start_secondary()
        return

    def get_fade_duration(self):
        if self.fade == FADE_IN:
            return PAINT_SECONDARY_FADE_IN_DURATION
        else:
            if self.fade == FADE_OUT:
                return PAINT_SECONDARY_FADE_OUT_DURATION
            return 0.0
