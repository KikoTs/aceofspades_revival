from aoslib.gui import HandlerBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_WITH_BOX
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.gui.menuOptionControl import MenuOptionControl
from aoslib.text import medium_aldo_ui_font
from shared.hud_constants import DROPDOWN_BOX_SPACING
from aoslib.images import global_images
from aoslib.media import HUD_AUDIO_ZONE

class DropBoxControl(HandlerBase):

    def initialize(self, manager, rows, selected_index, x, y, width, height, noof_visible_rows, row_height=20):
        if rows is not None and selected_index >= 0 and selected_index < len(rows):
            text = rows[selected_index]
        else:
            text = ''
        self.manager = manager
        self.title_bar = MenuOptionControl(text, x, y, width, height, self.on_open_menu_button_click, global_images.down_arrow)
        self.title_bar.center_text = False
        self.list_panel = ListPanelBase(manager)
        self.list_panel.list_spacing = DROPDOWN_BOX_SPACING
        self.list_panel.current_row_index = selected_index
        self.focus_gained_handler = None
        self.focus_lost_handler = None
        self.selected = False
        self.over = False
        self.x = x
        self.y = y
        self.width = width
        self.row_height = row_height
        self.noof_visible_rows = noof_visible_rows
        self.list_panel.set_background(BACKGROUND_WITH_BOX)
        self.visible = True
        self.update_rows(rows, selected_index, True)
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        return

    def setup_list_panel(self):
        total_height = self.row_height * self.noof_visible_rows
        self.list_panel.initialise_ui(None, self.x, self.y - 1, self.width, total_height, row_height=self.row_height)
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        return

    def update_rows(self, rows, selected_index, fire_event=False):
        self.setup_list_panel()
        self.list_panel.rows = []
        for row_text in rows:
            list_item = ListPanelItemBase()
            list_item.name = row_text
            list_item.center_text = False
            self.list_panel.rows.append(list_item)

        if selected_index >= 0 and selected_index < len(self.list_panel.rows):
            self.list_panel.select_row(self.list_panel.rows[selected_index], silent=True, fire_selected_row_event=fire_event)
            self.title_bar.name = self.list_panel.rows[selected_index].name
        else:
            self.title_bar.name = ''

    def add_focus_gained_handler(self, handler):
        self.focus_gained_handler = handler

    def add_focus_lost_handler(self, handler):
        self.focus_lost_handler = handler

    def get_selected_index(self):
        return self.list_panel.current_row_index

    def set_index(self, index):
        if self.list_panel is None or self.title_bar is None:
            return
        if index < 0 or index >= len(self.list_panel.rows):
            return
        self.list_panel.select_row(self.list_panel.rows[index], True, False)
        self.title_bar.name = self.list_panel.rows[index].name
        return

    def get_row_value_for_index(self, index):
        noof_rows = len(self.list_panel.rows)
        if noof_rows == 0 or index >= noof_rows or index < 0:
            return None
        return self.list_panel.rows[index].name

    def update_position(self, x, y, width, height):
        self.title_bar.update_position(x, y, width, height)
        self.list_panel.update_position(x, y, width, self.list_panel.height)
        self.list_panel.on_scroll(0, True)

    def set_enabled(self, enabled):
        super(DropBoxControl, self).set_enabled(enabled)
        self.title_bar.set_enabled(enabled)
        self.close_drop_down()

    def on_open_menu_button_click(self):
        if self.selected:
            if self.manager.media:
                self.manager.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
            self.close_drop_down()
        elif self.manager.media:
            self.manager.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.open_drop_down()

    def open_drop_down(self, silent=False):
        if not self.selected:
            self.selected = True
            if self.focus_gained_handler and not silent:
                self.focus_gained_handler(self)

    def close_drop_down(self, silent=False):
        if self.selected:
            self.selected = False
            if self.focus_lost_handler and not silent:
                self.focus_lost_handler(self)

    def on_row_selected(self, index, row):
        self.title_bar.name = row.name
        self.fire_handlers(self.list_panel.current_row_index)
        self.close_drop_down()

    def draw(self):
        if self.visible:
            self.title_bar.draw()
            if self.selected:
                self.list_panel.draw()

    def update_over(self, x, y):
        if self.title_bar.get_mouse_collides(x, y) or self.list_panel.get_mouse_collides(x, y, include_scrollbar=True):
            self.over = True
        else:
            self.over = False

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.visible:
            self.title_bar.on_mouse_drag(x, y, dx, dy, button, modifiers)
            if self.selected:
                self.list_panel.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        self.update_over(x, y)
        if not self.over and self.selected:
            self.close_drop_down()
        if self.visible:
            self.title_bar.on_mouse_press(x, y, button, modifiers)
            if self.selected:
                self.list_panel.on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)
        if self.visible:
            self.title_bar.on_mouse_motion(x, y, dx, dy)
            if self.selected:
                self.list_panel.on_mouse_motion(x, y, dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        self.update_over(x, y)
        if self.visible and self.over:
            self.title_bar.on_mouse_release(x, y, button, modifiers)
            if self.selected:
                self.list_panel.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.visible:
            if self.selected:
                self.list_panel.on_mouse_scroll(x, y, dx, dy)
