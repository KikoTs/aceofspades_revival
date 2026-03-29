from aoslib.scenes.frontend.tabBase import TabBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.settingsSliderListItem import SettingsSliderListItem
from aoslib.scenes.main.settingsToggleListItem import SettingsToggleListItem
from aoslib.scenes.main.settingsDropdownBoxListItem import SettingsDropdownListItem
from aoslib.images import global_images
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from shared.common import clamp, A2285
from shared.hud_constants import SETTINGS_ROW_HEIGHT, SETTINGS_ROW_SPACING
from aoslib.config import GRAPHICS_DEFAULT
from shared.constants import DRAW_DISTANCE_HIGH, MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font
from shared.hud_constants import TEXT_BACKGROUND_SPACING
import aoslib.graphicsManager as graphics_manager, pyglet
the_graphics_manager = graphics_manager.graphics_manager
import aoslib.image as aosimage, aoslib.images as aosimages, shared.constants as constants

class GraphicsTab(TabBase):
    content_frame = global_images.graphics_settings_frame
    orig_detail_level_value = 2
    orig_texture_quality_value = 1
    orig_model_detail_value = 2
    original_resolution = 0

    def initialize(self):
        self.x = 152
        self.y = 467
        self.width = 494
        self.height = 293
        self.elements = []
        self.controls_enabled = True
        self.list_panel = ListPanelBase(self.manager)
        self.list_panel.initialise_ui('', self.x, self.y, self.width, self.height, row_height=SETTINGS_ROW_HEIGHT)
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.line_spacing = SETTINGS_ROW_SPACING
        self.elements.append(self.list_panel)
        self.resolution_row = None
        self.in_game_tab = False
        cfg = self.config
        self.draw_distance_map = A2285
        the_graphics_manager.graphics_tab_resolutions_populate_callback = self.populate_items
        self.populate_items()
        return

    def populate_items(self, modified_index=False, current_index=0):
        self.list_panel.rows = []
        cfg = self.config
        if modified_index:
            self.set_original_resolution(current_index)
        options = ()
        for resolutions in cfg.sorted_screen_resolutions_for_gui:
            options += (resolutions[1].resolution_string,)

        self.resolution_row = SettingsDropdownListItem(strings.RESOLUTION, 'resolution', options, self.manager, cfg.resolution, self.set_config)
        self.list_panel.rows.append(self.resolution_row)
        self.orig_antialias_value = cfg.antialias
        if the_graphics_manager.is_msaa_supported:
            options = (
             strings.OFF, '2', '4')
            row = SettingsSliderListItem(strings.ANTIALIAS, 'antialias', options, cfg.antialias, self.set_config, self.media)
            self.list_panel.rows.append(row)
        options = (strings.LOW, strings.MEDIUM, strings.HIGH)
        row = SettingsSliderListItem(strings.EFFECT_QUALITY, 'effect_quality', options, cfg.effect_quality, self.set_config, self.media)
        self.list_panel.rows.append(row)
        row = SettingsSliderListItem(strings.DRAW_DISTANCE, 'draw_distance', options, self.get_draw_distance_index(), self.set_config, self.media)
        self.list_panel.rows.append(row)
        if constants.USE_GLSL:
            detail_value = self.orig_detail_level_value = clamp(cfg.detail_level, -1, 2)
            row = SettingsSliderListItem(strings.SHADER_QUALITY, 'detail_level', options, detail_value, self.set_config, self.media)
            self.list_panel.rows.append(row)
        else:
            detail_value = -1
        value = self.orig_texture_quality_value = clamp(cfg.texture_quality, 0, 2)
        row = SettingsSliderListItem(strings.TEXTURE_QUALITY, 'texture_quality', options, value, self.set_config, self.media)
        self.list_panel.rows.append(row)
        value = self.orig_model_detaily_value = clamp(cfg.model_detail, 0, 2)
        row = SettingsSliderListItem(strings.GRAPHICS_QUALITY, 'model_detail', options, value, self.set_config, self.media)
        self.list_panel.rows.append(row)
        row = SettingsToggleListItem(strings.VSYNC, 'vsync', cfg.vsync, self.set_toggle_option_config)
        self.list_panel.rows.append(row)
        aa_value = True if detail_value < 0 else False
        row = SettingsToggleListItem(strings.COMPATIBILTY_SHADER, 'arb_shader', aa_value, self.set_toggle_option_config)
        self.list_panel.rows.append(row)
        for row in self.list_panel.rows:
            row.set_enabled(not self.in_game_tab)
            row.enable_on_scroll = False

        self.list_panel.on_scroll(0, silent=True)
        self.resolution_row.control.list_panel.recreate_scrollbar()

    def on_mouse_release(self, x, y, button, modifiers):
        if self.resolution_row is not None and self.resolution_row.enabled:
            self.resolution_row.control.on_mouse_release(x, y, button, modifiers)
            if self.resolution_row.control.selected:
                return
        super(GraphicsTab, self).on_mouse_release(x, y, button, modifiers)
        return

    def on_mouse_press(self, x, y, button, modifiers):
        if self.resolution_row is not None and self.resolution_row.enabled:
            self.resolution_row.control.on_mouse_press(x, y, button, modifiers)
            if self.resolution_row.control.selected:
                return
        super(GraphicsTab, self).on_mouse_press(x, y, button, modifiers)
        return

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.resolution_row is not None and self.resolution_row.enabled:
            self.resolution_row.control.on_mouse_scroll(x, y, dx, dy)
            if self.resolution_row.control.selected:
                return
        super(GraphicsTab, self).on_mouse_scroll(x, y, dx, dy)
        return

    def on_mouse_motion(self, x, y, dx, dy):
        if self.resolution_row is not None and self.resolution_row.enabled:
            self.resolution_row.control.on_mouse_motion(x, y, dx, dy)
            if self.resolution_row.control.selected:
                return
        super(GraphicsTab, self).on_mouse_motion(x, y, dx, dy)
        return

    def draw(self):
        for element in self.elements:
            element.draw()

        if self.resolution_row is not None and self.resolution_row.visible and self.resolution_row.control:
            self.resolution_row.control.draw()
            x = self.resolution_row.control.title_bar.x + TEXT_BACKGROUND_SPACING
            text = strings.FULLSCREEN
            if not self.config.fullscreen:
                text = strings.WINDOWED
            draw_text_with_alignment_and_size_validation('(' + text.lower() + ')', x, self.resolution_row.y1, self.resolution_row.control.title_bar.text_width, self.resolution_row.height, MENU_FONT_COLOR, small_standard_ui_font, alignment_x='right', alignment_y='center')
        return

    def get_draw_distance_index(self):
        for index, item in self.draw_distance_map.iteritems():
            if item == self.config.draw_distance:
                return index

        return 0

    def set_toggle_option_config(self, value, config_name):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        config_value = True if value > 0 else False
        self.config.set(config_name, config_value)

    def set_config(self, value, value_as_string, config_name):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        if config_name == 'draw_distance':
            if value >= 0 and value < len(A2285):
                config_value = A2285[value]
            else:
                config_value = A2285[DRAW_DISTANCE_HIGH]
        else:
            config_value = value
        self.config.set(config_name, config_value)

    def set_original_resolution(self, original_resolution):
        self.original_resolution = original_resolution
        if self.resolution_row is not None:
            self.resolution_row.set_value(original_resolution)
        return

    def on_change(self, config_name, control):
        pass

    def on_defaults_pressed(self):
        pass

    def update_display(self):
        for row in self.list_panel.rows:
            row.set_enabled(not self.in_game_tab)

    def apply_changes(self):
        cfg = self.config
        needs_restart = False
        aa_value = self.get_row_value('antialias')
        if aa_value != self.orig_antialias_value and the_graphics_manager.is_msaa_supported and aa_value is not None:
            needs_restart = True
        for id in ['antialias', 'effect_quality', 'draw_distance', 'vsync']:
            value = self.get_row_value(id)
            if value is not None:
                if id == 'vsync':
                    config_value = True if value > 0 else False
                elif id == 'draw_distance':
                    if value >= 0 and value < len(A2285):
                        config_value = A2285[value]
                    else:
                        config_value = A2285[DRAW_DISTANCE_HIGH]
                else:
                    config_value = value
                cfg.set(id, config_value)

        texture_quality_value = self.get_row_value('texture_quality')
        if texture_quality_value != self.orig_texture_quality_value and texture_quality_value is not None:
            cfg.set('texture_quality', texture_quality_value)
            needs_restart = True
        model_detail_value = self.get_row_value('model_detail')
        if model_detail_value != self.orig_model_detail_value and model_detail_value is not None:
            cfg.set('model_detail', model_detail_value)
            needs_restart = True
        detail_level = self.get_row_value('detail_level')
        if detail_level != self.orig_detail_level_value:
            cfg.set('detail_level', detail_level)
            needs_restart = True
        arb_shader_value = self.get_row_value('arb_shader')
        if arb_shader_value and detail_level is not -1:
            self.set_row_value('detail_level', -1)
            cfg.set('detail_level', -1)
            needs_restart = True
        elif not arb_shader_value and detail_level is -1 or detail_level is None:
            self.set_row_value('detail_level', 2)
            cfg.set('detail_level', 2)
            needs_restart = True
        defer_save = False
        old_resolution = self.original_resolution
        if self.resolution_row is not None:
            resolution_name = self.resolution_row.get_current_value_as_text()
            the_resolution = self.config.screen_resolutions_by_string[resolution_name]
            current_resolution_index = self.resolution_row.get_current_value()
            if old_resolution != current_resolution_index:
                cfg.set('resolution', current_resolution_index)
                if not cfg.fullscreen:
                    cfg.set('window_height', the_resolution.height)
                    cfg.set('window_width', the_resolution.width)
                else:
                    cfg.set('height', the_resolution.height)
                    cfg.set('width', the_resolution.width)
                defer_save = True
            the_graphics_manager.update_resolutions()
        if needs_restart:
            self.manager.big_text.text = strings.CHANGE_MSAA_SETTINGS + '\n'
            self.manager.big_text_timer = 5.0
        if self.manager.game_scene:
            self.manager.game_scene.set_new_max_particles()
            self.manager.game_scene.reload_particle_effect_textures()
        if defer_save:
            from changeResMenu import ChangeResolutionMenu
            self.manager.set_menu(ChangeResolutionMenu, config=cfg, in_game_menu=self.in_game_tab)
        else:
            cfg.save()
        return defer_save

    def get_values_from_config(self):
        pass

    def cancel_changes(self):
        self.config.restore()
        self.populate_items()

    def get_row_with_id(self, id):
        for row in self.list_panel.rows:
            if row.id == id:
                return row

        return

    def get_row_value(self, row_id):
        row = self.get_row_with_id(row_id)
        if row is not None:
            return row.get_current_value()
        else:
            return

    def set_row_value(self, row_id, value):
        row = self.get_row_with_id(row_id)
        if row is not None:
            row.set_value(value)
        return

    def set_defaults(self):
        for row in self.list_panel.rows:
            if row.id == 'arb_shader':
                default_value = 0
            elif row.id not in GRAPHICS_DEFAULT:
                continue
            else:
                default_value = GRAPHICS_DEFAULT[row.id]
                if row.id == 'draw_distance':
                    for key, value in A2285.iteritems():
                        if value == default_value:
                            default_value = key

                if default_value == True or default_value == False:
                    default_value = 0 if GRAPHICS_DEFAULT[row.id] == False else 1
            row.set_value(default_value)
