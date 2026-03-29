from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.panelBase import PanelBase
from aoslib.scenes.main.ugcMapListItem import UGCMapListItem, MAP_STATE_UNPUBLISHED, MAP_STATE_DATA_REQUIRED, MAP_STATE_PUBLISHED, MAP_STATE_CHANGED
from aoslib import strings
from aoslib.ugc_data import get_publishable_game_modes, get_unpublishable_game_modes_with_reasons, get_ugc_data_from_file, has_been_published_previously, has_been_modified_since_publishing, get_hosted_ugc_map_names

class UGCMapsListPanel(PanelBase):

    def initialize(self):
        super(UGCMapsListPanel, self).initialize()
        self.maps_list = ListPanelBase(self.manager)
        self.selected_map_name_uid = None
        return

    def initialise_ui(self, x, y, width, height, on_row_selected_callback=None):
        super(UGCMapsListPanel, self).initialise_ui('', x, y, width, height)
        self.elements.append(self.maps_list)
        self.maps_list.initialise_ui(strings.MAP_LIST, x, y, width, height, has_header=True)
        self.on_row_selected_callback = on_row_selected_callback
        self.maps_list.add_on_item_selected_handler(self.on_row_selected, 0)
        self.__initialise()

    def on_row_selected(self, index, row):
        if row is None:
            return
        else:
            self.selected_map_name_uid = row.uid
            if self.on_row_selected_callback is not None:
                self.on_row_selected_callback(index, row)
            return

    def close(self):
        for row in [row for row in self.maps_list.rows if hasattr(row, 'close')]:
            row.close()

        return super(UGCMapsListPanel, self).close()

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
        first_row_uid = None
        for filename in get_hosted_ugc_map_names():
            if first_row_uid is None:
                first_row_uid = filename
            data = get_ugc_data_from_file(filename)
            if 'title' in data:
                map_title = data['title']
            else:
                map_title = filename
            publishable_modes = get_publishable_game_modes(data)
            unpublishable_modes = get_unpublishable_game_modes_with_reasons(data)
            if len(publishable_modes) == 0:
                state = MAP_STATE_DATA_REQUIRED
            elif has_been_published_previously(data):
                if has_been_modified_since_publishing(data):
                    state = MAP_STATE_CHANGED
                else:
                    state = MAP_STATE_PUBLISHED
            else:
                state = MAP_STATE_UNPUBLISHED
            row = UGCMapListItem(map_title, state, publishable_modes, unpublishable_modes, uid=filename)
            self.maps_list.rows.append(row)

        self.maps_list.on_scroll(0, silent=True)
        if self.selected_map_name_uid is None:
            self.selected_map_name_uid = first_row_uid
        row = self.maps_list.select_row_with_uid(self.selected_map_name_uid)
        if row is not None:
            self.on_row_selected(0, row)
        return

    def draw(self):
        if self.visible == False:
            return
        super(UGCMapsListPanel, self).draw()
        for element in self.elements:
            element.draw()
