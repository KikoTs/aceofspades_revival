from shared.glm import Vector3
from aoslib.animations.animation import Animation
from pyglet.gl import *
from aoslib import media
from shared.constants import *
from shared.hud_constants import *
from aoslib.text import equipped_tool_tip_font, get_resized_font_and_formatted_text_to_fit_boundaries
from aoslib import strings

class Tool(object):
    name = 'Tool'
    model = []
    model_display_lists = []
    model_size = 1.3 * BODY_PARTS_SIZE
    view_model_size = 0.05
    view_model = []
    icon = None
    image = None
    shoot_interval = None
    secondary_shoot_interval = None
    shoot_sound = None
    play_shoot_sound = True
    has_primary = has_secondary = True
    delay = delay_secondary = False
    pitch_initial = 0
    pitch_increase = 0
    use_color = False
    use_team_color = False
    use_other_team_color = False
    flash_with_spawn_protection = False
    count = 0
    default_count = 0
    initial_count = 0
    restock_amount = 0
    rotate_arm_ratio = 1.0
    model_scale = 1.0
    hold_side = False
    sight = None
    show_crosshair = HAS_AMMO_CROSSHAIR
    show_crosshair_centre = True
    can_zoom = True
    zoomed_sensitivity_factor = 0.5
    zoom = WEAPON_ZOOM
    draw_ammo = True
    shoot_delay = 0.0
    secondary_shoot_delay = 0.0
    active_primary = False
    active_secondary = False
    can_shoot_primary_while_sprinting = False
    can_shoot_secondary_while_sprinting = False
    tracer = None
    fps_position_offset = None
    never_pullout = False

    def __init__(self, character):
        self.equipped_tool_tip_text = strings.EQUIPPED_TOOL_TIP_DEFAULT
        self.equipped_tool_tip_font = equipped_tool_tip_font
        resized_font, lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.equipped_tool_tip_text, EQUIPPED_TOOL_TIP_WIDTH, EQUIPPED_TOOL_TIP_HEIGHT, self.equipped_tool_tip_font, EQUIPPED_TOOL_TIP_LINE_SPACING)
        self.equipped_tool_tip_font_resized = resized_font
        self.ammo_image = self.image
        self.animations = {}
        self.character = character
        self.pitch = self.pitch_initial
        self.initial_position = []
        self.initial_orientation = []
        self.position = []
        self.orientation = []
        self.animation_position_offset = []
        self.animation_orientation_offset = []
        self.zoom_position_offset = []
        self.zoom_orientation_offset = []
        for model_index in range(len(self.view_model)):
            self.initial_position.append(Vector3(0.0, 0.0, 0.0))
            self.initial_orientation.append(Vector3(0.0, 0.0, 0.0))
            self.position.append(self.initial_position[model_index])
            self.orientation.append(self.initial_orientation[model_index])
            self.animation_position_offset.append(Vector3(0.0, 0.0, 0.0))
            self.animation_orientation_offset.append(Vector3(0.0, 0.0, 0.0))
            self.zoom_position_offset.append(Vector3(0.0, 0.0, 0.0))
            self.zoom_orientation_offset.append(Vector3(0.0, 0.0, 0.0))

        self.arms_position_offset = Vector3(0.0, 0.0, 0.0)
        self.arms_orientation_offset = Vector3(0.0, 0.0, 0.0)

    def set_equipped_tool_tip_text(self, text):
        self.equipped_tool_tip_text = text
        resized_font, lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.equipped_tool_tip_text, EQUIPPED_TOOL_TIP_WIDTH, EQUIPPED_TOOL_TIP_HEIGHT, self.equipped_tool_tip_font, EQUIPPED_TOOL_TIP_LINE_SPACING)
        self.equipped_tool_tip_font_resized = resized_font

    def get_map_icon(self, viewer):
        return

    def reset_position(self, model_index):
        self.position[model_index] = self.initial_position[model_index].copy()

    def reset_orientation(self, model_index):
        self.orientation[model_index] = self.initial_orientation[model_index].copy()

    def play_sound(self, name, zone=media.DEFAULT_AUDIO_ZONE, loops=1, position=None, force_non_positional=False):
        return self.character.play_sound(name, volume=0.5, pos=position, zone=zone, loops=loops, force_non_positional=force_non_positional)

    def update(self, dt):
        if self.shoot_delay > 0:
            self.shoot_delay -= dt
        if self.secondary_shoot_delay > 0:
            self.secondary_shoot_delay -= dt
        self.update_animations(dt)
        if self.is_active():
            self.pitch = self.pitch + self.pitch_increase * dt
        else:
            self.pitch = self.pitch_initial

    def apply_transform(self, model_index, apply_animation_position=True, apply_animation_orientation=True):
        if model_index >= len(self.position) or model_index >= len(self.orientation):
            return
        position = self.position[model_index]
        orientation = self.orientation[model_index]
        if apply_animation_position or apply_animation_orientation:
            self.apply_animations(model_index)
            if apply_animation_position:
                position += self.animation_position_offset[model_index]
            if apply_animation_orientation:
                orientation += self.animation_orientation_offset[model_index]
        glTranslatef(position.x, position.y, position.z)
        glRotatef(orientation.x, 1.0, 0.0, 0.0)
        glRotatef(orientation.y, 0.0, 1.0, 0.0)
        glRotatef(orientation.z, 0.0, 0.0, 1.0)

    def get_arms_position(self):
        if len(self.model) > 0:
            return self.position[0] + self.animation_position_offset[0] + self.arms_position_offset
        else:
            return Vector3(0, 0, 0)

    def get_arms_orientation(self):
        if len(self.model) > 0:
            return self.orientation[0] + self.animation_orientation_offset[0] + self.arms_orientation_offset
        else:
            return Vector3(0, 0, 0)

    def update_animations(self, dt):
        for animation in self.animations.itervalues():
            animation.update(dt)

    def apply_animations(self, model_index):
        self.animation_position_offset[model_index] = Vector3(0.0, 0.0, 0.0)
        self.animation_orientation_offset[model_index] = Vector3(0.0, 0.0, 0.0)
        for animation in self.animations.itervalues():
            if animation.is_playing():
                self.animation_position_offset[model_index] += animation.get_position()
                self.animation_orientation_offset[model_index] += animation.get_orientation()

    def is_active(self):
        return self.active_primary or self.active_secondary

    def can_shoot_primary(self):
        return self.shoot_delay <= 0

    def can_shoot_secondary(self):
        return self.secondary_shoot_delay <= 0

    def use_primary(self):
        self.shoot_delay = self.shoot_interval

    def use_secondary(self):
        self.secondary_shoot_delay = self.secondary_shoot_interval

    def use_custom(self):
        return False

    def restock(self, type=None):
        if type == AMMO_CRATE:
            self.count = min(self.count + self.restock_amount, self.default_count)
        else:
            self.count = self.initial_count
        self.update_ammo()

    def get_pitch(self, dt, name):
        return self.pitch

    def on_stop_primary(self):
        self.active_primary = False

    def on_stop_secondary(self):
        self.active_secondary = False

    def on_start_primary(self):
        self.active_primary = True

    def on_start_secondary(self):
        self.active_secondary = True

    def get_weapon(self, klass):
        return self.character.get_weapon(klass)

    def on_set(self):
        pass

    def on_unset(self):
        self.shoot_delay = 0
        self.on_zoom(0)

    def needs_player_arms_drawing(self):
        return True

    def can_draw_ghosting(self):
        return self.character.block_count > 0 or self.character.parent.team and self.character.parent.team.infinite_blocks

    def draw_ghosting(self):
        return False

    def update_ammo(self):
        self.character.scene.hud.update_ammo()

    def get_ammo(self):
        return (
         self.count, None)

    def get_has_enough_ammo(self):
        return self.count >= 0

    def is_available(self):
        return True

    def is_reloadable(self):
        return False

    def can_reload_while_zoomed(self):
        return False

    def can_swap(self):
        return not self.is_active()

    def draw(self, tool_display, frustum_check=True):
        pass

    def draw_fps(self, weapon_display):
        pass

    def draw_manned(self):
        pass

    def can_display(self):
        return True

    def needs_zoom_arms_offset(self):
        return False

    def on_zoom(self, value):
        if value:
            for model_index in xrange(len(self.view_model)):
                self.position[model_index] += self.zoom_position_offset[model_index]
                self.orientation[model_index] += self.zoom_orientation_offset[model_index]

        else:
            for model_index in xrange(len(self.view_model)):
                self.reset_position(model_index)
                self.reset_orientation(model_index)

    def get_arm_pitch_range(self):
        return (
         ARMS_PITCH_MINIMUM, ARMS_PITCH_MAXIMUM)

    def get_audio_pos(self):
        if self.character.main:
            return None
        else:
            return self.character.world_object.position.get()
