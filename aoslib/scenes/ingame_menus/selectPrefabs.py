from aoslib import strings
from aoslib.scenes.ingame_menus.selectUGC import SelectUGC
from aoslib.images import global_images
from shared.constants_prefabs import A3053
from collections import namedtuple

class SelectPrefabs(SelectUGC):
    title = strings.PREFABS_MENU
    image_offset = [1.5, 5.0]
    selected_image_offset = [0.0, 2.0]

    def create_tabs(self):
        Tab = namedtuple('Tab', 'text table_index unselected_image selected_image')
        for index, tag in enumerate(sorted(self.prefabs_by_tag.keys())):
            self.tabs.append(Tab(strings.get_by_id(A3053[tag]), index, global_images.pf_unselected_tab, global_images.pf_selected_tab))

        super(SelectPrefabs, self).create_tabs()

    def draw_panel(self):
        global_images.pf_template_bg.blit(400, 325)

    def on_key_press(self, symbol, modifiers):
        super(SelectPrefabs, self).on_key_press(symbol, modifiers)
