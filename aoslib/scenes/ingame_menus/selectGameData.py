from aoslib import strings
from aoslib.scenes.ingame_menus.selectUGC import SelectUGC
from aoslib.images import global_images
from collections import namedtuple

class SelectGameData(SelectUGC):
    title = strings.UGC_GAME_DATA
    image_offset = [0.0, -13.0]
    selected_image_offset = [0.0, 4.0]

    def create_tabs(self):
        Tab = namedtuple('Tab', 'text table_index unselected_image selected_image')
        for index, category in enumerate(self.ugc_items_by_tag.keys()):
            self.tabs.append(Tab(strings.get_by_id(category), index + len(self.prefabs_by_tag.keys()), global_images.gdata_unselected_tab, global_images.gdata_selected_tab))

        super(SelectGameData, self).create_tabs(len(self.prefabs_by_tag.keys()))

    def draw_panel(self):
        global_images.gdata_template_bg.blit(235, 325)

    def on_key_press(self, symbol, modifiers):
        super(SelectGameData, self).on_key_press(symbol, modifiers, exit_menu_key=self.config.change_team)
