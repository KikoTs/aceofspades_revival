from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib import strings
from aoslib.text import draw_text_with_size_validation, draw_text_with_alignment_and_size_validation, medium_aldo_ui_font
from aoslib.gui import gl, TextButton
from shared.constants import MENU_FONT_DISABLED_COLOR
from shared.constants_shop import DLC_APPID_LIST
import playlists

class OwnableItemBase(ListPanelItemBase):

    def initialize(self, name, dlc_manager, selectable_when_unowned=False, owned=None, playlist_id=None, pack_name='', filename=None, uid=None, custom_map=False, author=''):
        super(OwnableItemBase, self).initialize(name, uid=uid)
        self.filename = filename
        self.dlc_manager = dlc_manager
        self.custom_map = custom_map
        self.author = author
        if playlist_id is not None:
            self.demo = playlists.play_lists_by_id[playlist_id].demo
        else:
            self.demo = True
        self.show_unowned = show_as_unowned(name)
        if owned is not None:
            self.owned = owned
        else:
            self.owned = owns_info(name, dlc_manager, self.demo)
        self.selectable_when_unowned = selectable_when_unowned
        self.pack_name = pack_name
        if not self.owned:
            dlc_manager.append_dlc_installed_callback(self.on_dlc_installed)
        return

    def close(self):
        if not self.owned:
            self.dlc_manager.remove_dlc_installed_callback(self.on_dlc_installed)

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        text_width = self.width - self.pad * 2
        text_height = self.height - self.pad * 2
        x = self.get_text_x_position()
        y = self.get_text_y_position()
        if self.owned or self.selectable_when_unowned:
            colour = self.text_colour
        else:
            colour = MENU_FONT_DISABLED_COLOR
        if self.name != 'Untitled UGC':
            text = self.name
        else:
            text = self.filename
        draw_text_with_size_validation(text, x, y, text_width, text_height, colour, self.font, self.center_text)
        if not self.owned or self.show_unowned:
            colour = MENU_FONT_DISABLED_COLOR
            draw_text_with_alignment_and_size_validation(strings.NOT_OWNED, x, y, text_width - self.pad_x * 2, text_height, colour, medium_aldo_ui_font, 'right')
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)

    def is_selectable(self):
        return super(OwnableItemBase, self).is_selectable() and (self.owned or self.selectable_when_unowned)

    def on_dlc_installed(self, dlc_manager):
        previously_owned = self.owned
        self.owned = owns_info(self.name, dlc_manager, self.demo)
        if not previously_owned and self.owned:
            dlc_manager.remove_dlc_installed_callback(self.on_dlc_installed)


def owns_info(info, dlc_manager, demo=True):
    # If it's a demo version, certain content should be marked as owned
    if demo:
        return True
        
    dlc_to_info = {
        'mafia': ['Alcatraz', 'CityOfChicago', strings.TC_TITLE, strings.VIP_MODE_TITLE]
    }
    
    required_dlc = []
    
    # Check which DLC is required for the given info
    for dlc, info_list in dlc_to_info.iteritems():
        if info in info_list and dlc not in required_dlc:
            required_dlc.append(dlc)
    
    # Check if all required DLC is installed
    for dlc in required_dlc:
        if not dlc_manager.is_installed_dlc(dlc):
            return False
    
    return True

def show_as_unowned(info):
    return False
