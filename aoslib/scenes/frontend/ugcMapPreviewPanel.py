from aoslib.scenes.frontend.panelBase import PanelBase, BACKGROUND_NONE
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.ugcMapInfoListItem import *
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font
from aoslib.gui import TextButton
from shared.constants_gamemode import *
from shared.hud_constants import LIST_PANEL_SPACING, UI_CONTROL_BAR_BUTTON_SPACING, TEXT_BACKGROUND_SPACING, BLACK_COLOUR, RED_COLOUR
from shared.constants_ugc_objectives import UGC_OBJECTIVES_TYPES
from aoslib.images import global_images
from aoslib.draw import draw_quad
from aoslib import strings
from pyglet import gl

class UGCMapPreviewPanel(PanelBase):

    def initialize(self):
        super(UGCMapPreviewPanel, self).initialize()
        self.image = None
        self.list_panel = ListPanelBase(self.manager)
        self.delete_button = None
        self.on_delete_button_press_callback = None
        self.button_height = 25
        return

    def initialise_ui(self, title, x, y, width, height, image=None, image_height=70, has_header=True):
        super(UGCMapPreviewPanel, self).initialise_ui(title, x, y, width, height, has_header)
        self.image = image
        self.image_height = image_height
        self.list_panel.set_background(BACKGROUND_NONE)
        self.update_list_position()
        self.elements.append(self.list_panel)
        self.filename = None
        return

    def add_delete_button(self, on_delete_button_callback):
        if self.delete_button is None:
            y = self.y - self.height + LIST_PANEL_SPACING + self.button_height
            self.delete_button = TextButton(strings.DELETE, self.x + LIST_PANEL_SPACING, y, 80, self.button_height, 14)
            self.delete_button.tint = (0.7, 0.1, 0.1)
            self.delete_button.text_colour = (255, 255, 255, 255)
            self.delete_button.add_handler(self.on_delete_button_pressed)
            self.on_delete_button_press_callback = on_delete_button_callback
        if self.delete_button not in self.elements:
            self.elements.append(self.delete_button)
        return

    def on_delete_button_pressed(self):
        if self.on_delete_button_press_callback is not None:
            self.on_delete_button_press_callback()
        return

    def close(self):
        for row in [row for row in self.list_panel.rows if hasattr(row, 'close')]:
            row.close()

        return super(UGCMapPreviewPanel, self).close()

    def set_content_visibility(self, visible):
        self.visible = visible
        self.enabled = visible
        for element in self.elements:
            element.visible = visible

    def update_list_position(self):
        x = self.x
        width = self.width
        y = self.y
        height = self.height - self.button_height - LIST_PANEL_SPACING
        header_height = 0
        image_height = 0
        if self.has_header:
            header_height = self.title_height + LIST_PANEL_SPACING
        if self.image is not None:
            image_height = self.image_height + LIST_PANEL_SPACING
        y -= header_height + image_height
        height -= header_height + image_height
        self.list_panel.initialise_ui('', x, y, width, height)
        return

    def set_image(self, image):
        previous_image = self.image
        self.image = image
        if self.image != previous_image:
            self.update_info_list_position()

    def draw_image(self):
        if self.visible == False:
            return
        else:
            if self.image is None:
                return
            width = self.width - LIST_PANEL_SPACING * 2
            x = self.x + LIST_PANEL_SPACING + width / 2
            if self.has_header:
                y = self.y - LIST_PANEL_SPACING * 2 - self.title_height
            else:
                y = self.y - LIST_PANEL_SPACING
            image_scale_x = float(width) / float(self.image.width)
            image_scale_y = float(height) / float(self.image.height)
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            gl.glPushMatrix()
            gl.glTranslatef(x, y, 0)
            gl.glScalef(image_scale_x, image_scale_y, 0.0)
            self.image.blit(0, 0)
            gl.glPopMatrix()
            return

    def draw_delete_button_tooltip(self):
        if self.delete_button is None:
            return
        else:
            self.delete_button.visible = self.list_panel is not None and len(self.list_panel.rows) > 0
            if self.delete_button.visible == False:
                return
            x = self.delete_button.x + self.delete_button.width + UI_CONTROL_BAR_BUTTON_SPACING
            y = self.delete_button.y - self.delete_button.height + 2
            width = self.list_panel.width - self.delete_button.width - UI_CONTROL_BAR_BUTTON_SPACING - LIST_PANEL_SPACING * 2
            height = self.delete_button.height - 2
            draw_quad(x, y, width, height, BLACK_COLOUR)
            draw_text_with_alignment_and_size_validation(strings.DELETE_MAP_MESSAGE, x + TEXT_BACKGROUND_SPACING, y, width - TEXT_BACKGROUND_SPACING * 2, height, RED_COLOUR, small_standard_ui_font, alignment_x='center', alignment_y='center')
            return

    def draw(self):
        super(UGCMapPreviewPanel, self).draw()
        self.draw_image()
        for item in self.elements:
            item.draw()

        self.draw_delete_button_tooltip()

    def clear_display_data(self):
        self.image = None
        self.title = None
        del self.list_panel.rows[:]
        return

    def populate_list(self, publishable_modes, unpublishable_modes):
        if len(self.list_panel.rows) > 0:
            del self.list_panel.rows[:]
        for mode_id, mode_title in A2448.iteritems():
            if A2450[mode_id] in [A2445, A2447, A2435]:
                continue
            if mode_id in ('cctf', ):
                continue
            if A2450[mode_id] in publishable_modes:
                mode_state = MODE_STATE_COMPLETED
                reason_id = ''
            else:
                mode_state = MODE_STATE_DATA_REQUIRED
                unpublishable_reasons = unpublishable_modes.get(A2450[mode_id], [])
                try:
                    prioritised_reasons = sorted(unpublishable_reasons, key=(lambda reason: UGC_OBJECTIVES_TYPES[reason[0]]['priority']))
                    reason = prioritised_reasons[0]
                    reason_id = ('{}_{}').format(reason[0], reason[1].upper())
                except IndexError:
                    reason_id = ''

            row = UGCMapInfoListItem(strings.get_by_id(mode_title), mode_state, reason_id)
            self.list_panel.rows.append(row)

        self.list_panel.on_scroll(0, silent=True)
