from aoslib.scenes.main.matchSettingsListItem import MatchSettingsListItem
from aoslib.scenes.gui.editBoxControl import EditBoxControl
import re
from aoslib.ugc_data import get_does_title_exist
from aoslib.scenes.main.matchSettings import generate_ugc_map_title
from shared.steam import SteamGetCurrentLobby, SteamGetLobbyData

class MatchSettingsEditTextListItem(MatchSettingsListItem):

    def initialize(self, edit_text_value, display_name, settings_id, lobby_id, text_modified_callback=None, profanity_manager=None):
        super(MatchSettingsEditTextListItem, self).initialize(display_name, settings_id, lobby_id)
        self.original_text = edit_text_value
        self.text_modified_callback = text_modified_callback
        self.control = EditBoxControl(edit_text_value, self.x1, self.y1, self.width, self.height, center=False, profanity_manager=profanity_manager, replacement_words='*')
        self.control.on_return_callback = self.on_edit_text
        self.control.add_handler(self.on_edit_text)
        self.control.allow_over_typing = True
        self.elements.append(self.control)

    def reset(self, text):
        self.original_text = text
        self.control.set(text)

    def update_position(self, x, y, width, height, highlight_width):
        super(MatchSettingsEditTextListItem, self).update_position(x, y, width, height, highlight_width)
        self.control.initialise_text(self.original_text)

    def on_edit_text(self):
        if self.text_modified_callback is not None:
            if self.original_text != self.control.text:
                result = re.match('^.{4,32}$', self.control.text, flags=re.LOCALE)
                text = self.control.text
                if not result:
                    if self.original_text is None:
                        text = 'UGC Untitled'
                        self.original_text = text
                    self.control.set(self.original_text)
                    self.control.initialise_caret_index()
                else:
                    self.original_text = text
                if get_does_title_exist(text):
                    lobby_id = SteamGetCurrentLobby()
                    text = SteamGetLobbyData(lobby_id, 'MAP_ROTATION_ORIGINAL_TITLE')
                    text = generate_ugc_map_title(text)
                    self.original_text = text
                    self.control.set(text)
                    self.control.initialise_caret_index()
                self.text_modified_callback(text)
        return
