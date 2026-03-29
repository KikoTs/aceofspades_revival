from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.frontend.panelBase import PanelBase
from aoslib import strings
from aoslib.text import medium_standard_ui_font, get_resized_font_and_formatted_text_to_fit_boundaries, draw_text_lines
from aoslib.draw import draw_quad
from shared.hud_constants import LIST_PANEL_SPACING, UGC_TOOLTIP_BACKGROUND_COLOUR, UGC_TOOLTIP_TEXT_COLOUR, TEXT_BACKGROUND_SPACING, UI_CONTROL_SPACING
from aoslib.ugc_data import get_hosted_ugc_map_names

class UGCPublishedMapsPanel(PanelBase):

    def initialize(self):
        super(UGCPublishedMapsPanel, self).initialize()
        self.maps_list = ListPanelBase(self.manager)
        self.tooltip_height = 50
        self.selected_row = None
        self.font = medium_standard_ui_font
        self.tooltip_lines = []
        return

    def initialise_ui(self, x, y, width, height, on_row_selected_callback=None, on_row_unselected_callback=None, tooltip_height=50):
        super(UGCPublishedMapsPanel, self).initialise_ui('', x, y, width, height)
        self.elements.append(self.maps_list)
        self.selected_row = None
        self.tooltip_height = tooltip_height
        list_height = height - tooltip_height - LIST_PANEL_SPACING * 3 - TEXT_BACKGROUND_SPACING
        self.maps_list.initialise_ui(strings.PUBLISHED_MAPS, x, y, width, list_height, has_header=True)
        self.maps_list.allow_unselect_row_on_click = True
        self.on_row_selected_callback = on_row_selected_callback
        self.on_row_unselected_callback = on_row_unselected_callback
        self.maps_list.add_on_item_selected_handler(self.on_row_selected, 0)
        self.maps_list.add_on_item_unselected_handler(self.on_row_unselected, 0)
        self.__initialise()
        self.text_width = self.width - LIST_PANEL_SPACING * 2 - TEXT_BACKGROUND_SPACING * 2
        self.text_height = self.tooltip_height - UI_CONTROL_SPACING * 2
        self.font, self.tooltip_lines = get_resized_font_and_formatted_text_to_fit_boundaries(strings.UGC_OVERWRITE_WARNING, self.text_width, self.text_height, medium_standard_ui_font, 2)
        return

    def on_row_selected(self, index, row):
        self.selected_row = row
        if self.on_row_selected_callback is not None:
            self.on_row_selected_callback(index, row)
        return

    def on_row_unselected(self, index, row):
        self.selected_row = None
        if self.on_row_unselected_callback is not None:
            self.on_row_unselected_callback(index, row)
        return

    def close(self):
        for row in [row for row in self.maps_list.rows if hasattr(row, 'close')]:
            row.close()

        return super(UGCPublishedMapsPanel, self).close()

    def __initialise(self):
        self.populate_list()

    def set_content_visibility(self, visible):
        self.visible = visible
        self.enabled = visible
        if visible:
            self.__initialise()

    def populate_list(self):
        if len(self.maps_list.rows) > 0:
            del self.maps_list.rows[:]
        for filename in get_hosted_ugc_map_names():
            row = ListPanelItemBase(filename)
            row.center_text = False
            self.maps_list.rows.append(row)

        self.maps_list.on_scroll(0, silent=True)

    def draw(self):
        if self.visible == False:
            return
        else:
            super(UGCPublishedMapsPanel, self).draw()
            for element in self.elements:
                element.draw()

            if self.selected_row is not None and self.tooltip_lines is not None:
                x = self.x + LIST_PANEL_SPACING
                y = self.y - self.height + LIST_PANEL_SPACING
                draw_quad(x, y, self.width - LIST_PANEL_SPACING * 2, self.tooltip_height, UGC_TOOLTIP_BACKGROUND_COLOUR)
                draw_text_lines(self.tooltip_lines, x + TEXT_BACKGROUND_SPACING, y + UI_CONTROL_SPACING, self.text_width, self.text_height, self.font, 2.0, UGC_TOOLTIP_TEXT_COLOUR, 'center', 'center')
            return
