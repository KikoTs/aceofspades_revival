from aoslib.scenes.frontend.panelBase import PanelBase, BACKGROUND_NONE
from aoslib.gui import TextButton
from aoslib.draw import draw_quad
from shared.constants import MENU_FONT_COLOR
from shared.steam import SteamGetCurrentLobby
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font
from aoslib import strings
from shared.hud_constants import BLACK_COLOUR, TEXT_BACKGROUND_SPACING, UI_CONTROL_BAR_BUTTON_SPACING

class LobbyPanelBase(PanelBase):

    def initialize(self):
        super(LobbyPanelBase, self).initialize()
        self.default_panel = None
        self.default_button = None
        self.lobby_id = SteamGetCurrentLobby()
        return

    def set_content_visibility(self, visible):
        super(LobbyPanelBase, self).set_content_visibility(visible)
        self.enabled = visible

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(LobbyPanelBase, self).initialise_ui('', x, y, width, height, has_header=False)
        self.set_background(BACKGROUND_NONE)
        self.lobby_id = lobby_id

    def add_default_panel(self, x, y, width, height):
        self.default_panel = PanelBase(self.manager)
        self.default_panel.initialise_ui(None, x, y, width, height)
        self.default_panel.set_background(BACKGROUND_NONE)
        self.elements.append(self.default_panel)
        return

    def add_default_button(self, on_button_press_callback, x, y, button_width=80, button_height=25, font_size=14):
        self.default_button = TextButton(strings.DEFAULTS, x, y, button_width, button_height, font_size)
        self.default_button.add_handler(on_button_press_callback)
        self.elements.append(self.default_button)

    def draw_defaults_panel_tooltip(self):
        if self.default_button is None or self.default_panel is None:
            return
        x = self.default_button.x + self.default_button.width + UI_CONTROL_BAR_BUTTON_SPACING
        y = self.default_panel.y - self.default_panel.height + 2
        width = self.default_panel.width - self.default_button.width - UI_CONTROL_BAR_BUTTON_SPACING
        height = self.default_button.height - 2
        draw_quad(x, y, width, height, BLACK_COLOUR)
        draw_text_with_alignment_and_size_validation(strings.RESET_OPTIONS, x + TEXT_BACKGROUND_SPACING, y, width - TEXT_BACKGROUND_SPACING * 2, height, MENU_FONT_COLOR, small_standard_ui_font, alignment_x='center', alignment_y='center')
        return

    def draw(self):
        if self.visible_content == False:
            return
        super(LobbyPanelBase, self).draw()
        for element in self.elements:
            element.draw()

        self.draw_defaults_panel_tooltip()
