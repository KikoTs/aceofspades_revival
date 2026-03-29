from pyglet import gl
from aoslib.gui import HandlerBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib import strings
from aoslib.scenes.main.ugcObjectiveListItem import UGCObjectiveListItem
from shared.constants_ugc_objectives import UGC_OBJECTIVES_TYPES
from shared.hud_constants import ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR
from aoslib.text import draw_text_with_alignment_and_size_validation, translate_controls_in_message
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import TEXT_BACKGROUND_SPACING

class UGCObjectivesListPanel(HandlerBase):

    def initialize(self, manager, x, y, width, height, row_height=20, has_header=True, enable_background_resizing=False, transparent_items=False, frame_padding_height=0, show_game_settings_text=False, only_show_incomplete=False):
        self.manager = manager
        self.width = width
        self.height = height
        self.objectives_listpanel = ListPanelBase(self.manager)
        self.show_game_settings_text = show_game_settings_text
        if transparent_items:
            row1_colour = (
             ROW_GREY_COLOUR[0], ROW_GREY_COLOUR[1], ROW_GREY_COLOUR[2], 120)
            row2_colour = (ROW_DARK_GREY_COLOUR[0], ROW_DARK_GREY_COLOUR[1], ROW_DARK_GREY_COLOUR[2], 120)
        else:
            row1_colour = ROW_GREY_COLOUR
            row2_colour = ROW_DARK_GREY_COLOUR
        self.row_colours = [
         row1_colour, row2_colour]
        self.frame_padding_height = frame_padding_height
        self.objectives_listpanel.initialise_ui(None, x, y, width, height, list_items_background_colors=self.row_colours, row_height=row_height, has_header=has_header, enable_background_resizing=enable_background_resizing)
        self.objectives_listpanel.title_width = width - 50
        self.only_show_incomplete = only_show_incomplete
        if self.only_show_incomplete:
            self.objectives_listpanel.title = strings.UGC_INCOMPLETE_OBJECTIVES_TITLE
        else:
            self.objectives_listpanel.title = strings.UGC_TAB_OBJECTIVES_TITLE
        if self.show_game_settings_text:
            self.objectives_listpanel.frame_padding_height = self.frame_padding_height
        self.elements = []
        self.elements.append(self.objectives_listpanel)
        self.objectives = {}
        self.scene = self.manager.game_scene
        self.scene.ugc_objectives_callbacks.append(self.update_objectives)
        self.temp_item = None
        self.update_objectives(self.scene.ugc_objectives)
        return

    def update_objectives(self, objectives):
        self.objectives = self.scene.ugc_objectives
        del self.objectives_listpanel.rows[:]
        self.temp_item = UGCObjectiveListItem('UGC_OBJECTIVE_AMMOCRATE_SPAWNS', 0)
        self.temp_item.update_position(0, 0, self.width, self.height, 0)
        for key, value in sorted(self.objectives.iteritems(), key=(lambda objective: UGC_OBJECTIVES_TYPES[objective[0]]['priority'])):
            item = UGCObjectiveListItem(key, value)
            if self.only_show_incomplete and not item.get_is_complete():
                self.objectives_listpanel.rows.append(item)
            elif not self.only_show_incomplete:
                self.objectives_listpanel.rows.append(item)

        self.objectives_listpanel.on_scroll(0, silent=True)

    def set_position_size(self, x, y, width, height, row_height=20, has_header=True, enable_background_resizing=False):
        self.width = width
        self.height = height
        self.objectives_listpanel.initialise_ui(None, x, y, width, height, row_height=row_height, list_items_background_colors=self.row_colours, has_header=has_header, enable_background_resizing=enable_background_resizing)
        self.objectives_listpanel.title_width = width - 50
        if self.only_show_incomplete:
            self.objectives_listpanel.title = strings.UGC_INCOMPLETE_OBJECTIVES_TITLE
        else:
            self.objectives_listpanel.title = strings.UGC_TAB_OBJECTIVES_TITLE
        if self.show_game_settings_text:
            self.objectives_listpanel.frame_padding_height = self.frame_padding_height
        self.update_objectives(self.scene.ugc_objectives)
        return

    def draw(self):
        if not self.scene:
            return
        if len(self.objectives_listpanel.rows) > 0:
            for element in self.elements:
                element.draw()

        if self.scene.is_ugc_host() and self.show_game_settings_text and self.temp_item and self.temp_item.update_done:
            if len(self.objectives_listpanel.rows) > 0:
                panel_height = self.objectives_listpanel.height
            else:
                panel_height = 0
            width = self.objectives_listpanel.width + self.objectives_listpanel.frame_padding_width
            x = self.objectives_listpanel.x
            y = self.objectives_listpanel.y - self.objectives_listpanel.frame_padding_height / 2 - panel_height - 25
            font_to_use = self.temp_item.font_to_use
            force_scale = self.temp_item.force_scale
            text = translate_controls_in_message(self.scene.manager.game_scene, strings.UGC_GAME_SETTINGS_HINT)
            draw_text_with_alignment_and_size_validation(text, x, y, width, 20, MENU_FONT_COLOR, font_to_use, 'left', 'center', shadowed=True, stroked=True, forced_scale=force_scale)
