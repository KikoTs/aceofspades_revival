from aoslib.scenes.frontend.panelBase import PanelBase, BACKGROUND_NONE
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.main.ownableItemBase import OwnableItemBase
from aoslib.scenes.main.matchSettings import get_game_info_data, get_string_as_list, get_game_rules_and_values_list
from aoslib.gui import TextList, Label
from aoslib.images import global_images
from aoslib.text import small_aldo_ui_font, medium_aldo_ui_font, big_aldo_ui_font, medium_standard_ui_font, small_standard_ui_font, START_FONT, split_text_to_fit_screen, ALDO_FONT, draw_text_within_boundaries
from aoslib import strings
from pyglet import gl
from shared.steam import SteamGetLobbyData, SteamGetAllLobbyData
from shared.constants_gamemode import A2450, A2446
from shared.constants_prefabs import A3056
from shared.hud_constants import ROW_DARK_GREY_COLOUR, ROW_GREY_COLOUR, LIST_PANEL_SPACING
from aoslib.common import get_map_value_safe

class PreviewPanelBase(PanelBase):

    def initialize(self):
        super(PreviewPanelBase, self).initialize()
        self.image = None
        self.server_type = None
        self.center_header_text = True
        self.visible_image = True
        self.visible_content = True
        self.info_list = ExpandableListPanel(self.manager)
        self.dlc_description = None
        self.show_buy_button = False
        return

    def initialise_ui(self, title, x, y, width, height, image=None, has_header=False):
        super(PreviewPanelBase, self).initialise_ui(title, x, y, width, height, has_header)
        self.image = image
        self.image_height = 66
        self.server_type = None
        self.info_list.set_background(BACKGROUND_NONE)
        if strings.language == 'english':
            dlc_font_size = 12
        else:
            dlc_font_size = 11
        self.dlc_description = Label(x=x + width * 0.5, y=y - height + 110, width=width - 35, height=256, anchor_x='center', anchor_y='top', font_name=START_FONT, font_size=dlc_font_size, color=(255,
                                                                                                                                                                                                   255,
                                                                                                                                                                                                   255,
                                                                                                                                                                                                   255))
        dlc_description_text = strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_1) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_2) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_3) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_4) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_5) + '\n'
        self.dlc_description.text = split_text_to_fit_screen(self.dlc_description.font, dlc_description_text, self.dlc_description.width, 0)
        self.update_info_list_position()
        self.elements.append(self.info_list)
        return

    def close(self):
        for row in [row for row in self.info_list.rows if hasattr(row, 'close')]:
            row.close()

        return super(PreviewPanelBase, self).close()

    def update_info_list_position(self):
        x = self.x
        width = self.width
        y = self.y
        height = self.height
        header_height = 0
        image_height = 0
        if self.has_header:
            header_height = self.title_height + LIST_PANEL_SPACING
        if self.image is not None:
            image_height = self.image_height + LIST_PANEL_SPACING
        y -= header_height + image_height
        height -= header_height + image_height
        self.info_list.initialise_ui('', x, y, width, height)
        return

    def set_game_mode_image(self, mode_id):
        previous_image = self.image
        if mode_id == strings.RANDOM:
            self.image = global_images.mode_image_letterbox_random
        elif mode_id == 'multiple modes':
            self.image = global_images.mode_image_letterbox_multi_mode
        elif mode_id in global_images.mode_images_letterbox:
            self.image = global_images.mode_images_letterbox[mode_id]
        if self.image != previous_image:
            self.update_info_list_position()

    def draw_image(self, x, y, width, height):
        if self.image is None or self.visible_image == False:
            return
        image_scale_x = float(width) / float(self.image.width)
        image_scale_y = float(height) / float(self.image.height)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0)
        gl.glScalef(image_scale_x, image_scale_y, 0.0)
        self.image.blit(0, 0)
        gl.glPopMatrix()
        return

    def draw(self):
        super(PreviewPanelBase, self).draw()
        if self.visible_content == False:
            return
        else:
            width = self.width - LIST_PANEL_SPACING * 2
            x = self.x + LIST_PANEL_SPACING + width / 2
            if self.has_header:
                y = self.y - LIST_PANEL_SPACING * 2 - self.title_height
            else:
                y = self.y - LIST_PANEL_SPACING
            self.draw_image(x, y - self.image_height / 2, width, self.image_height)
            for item in self.elements:
                item.draw()

            unowned_rows = [row for row in self.info_list.rows if hasattr(row, 'owned') and not row.owned]
            if len(unowned_rows) > 0 or self.show_buy_button:
                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                if self.dlc_description is not None:
                    self.dlc_description.draw()
            return

    def clear_display_data(self):
        self.image = None
        self.server_type = None
        self.title = None
        self.info_list.reset_list()
        return

    def set_display_data(self, game_modes, rules, collapse_rows=False, game_info_text=strings.GAME_INFO, rules_text=strings.GAME_RULES):
        current_index = self.info_list.min_index
        game_info_category = self.info_list.find_row_with_name(game_info_text)
        if game_info_category is None:
            game_info_expanded = True
        else:
            game_info_expanded = game_info_category.is_expanded
        game_rules_category = self.info_list.find_row_with_name(rules_text)
        if game_rules_category is None:
            game_rules_expanded = True
        else:
            game_rules_expanded = game_rules_category.is_expanded
        self.info_list.reset_list()
        noof_category_rows = 0
        if len(game_modes) > 0:
            self.add_category(game_info_text, game_modes, game_info_expanded)
            noof_category_rows += 1
        if len(rules) > 0 and len(self.info_list.rows) > 0:
            self.add_category(rules_text, rules, game_rules_expanded)
            noof_category_rows += 1
        if noof_category_rows > 1 and collapse_rows:
            self.info_list.expand_all(False)
        self.info_list.on_scroll(current_index, silent=True)
        self.info_list.scrollbar.set_scroll(self.info_list.min_index, silent=True)
        return

    def update_display_data(self, lobby_id):
        lobby_data = SteamGetAllLobbyData(lobby_id)
        game_modes_string = get_map_value_safe(lobby_data, 'PLAYLIST')
        map_rotation_string = get_map_value_safe(lobby_data, 'MAP_ROTATION_NEW_TITLE')
        game_modes = get_string_as_list(game_modes_string)
        map_rotation = get_string_as_list(map_rotation_string)
        noof_modes = len(game_modes)
        if noof_modes > 1:
            mode_id = 'multiple modes'
            self.set_game_mode_image(mode_id)
        elif noof_modes == 1:
            if game_modes[0] == 'cctf':
                mode_id = A2446
            else:
                mode_id = A2450[game_modes[0]]
            self.set_game_mode_image(mode_id)
        game_info = get_game_info_data(lobby_id, game_modes)
        rules = get_game_rules_and_values_list(lobby_id)
        prefab_set_id_string = get_map_value_safe(lobby_data, 'PREFAB_SET', silent=True)
        if prefab_set_id_string and prefab_set_id_string != '':
            prefab_set_id = int(prefab_set_id_string)
            if prefab_set_id in A3056.keys():
                text = strings.PREFAB_SET + ': ' + strings.get_by_id(A3056[prefab_set_id])
                game_info.append(text)
        self.set_display_data(game_info, rules)
        noof_rows = len(self.info_list.rows)
        current_index = self.info_list.min_index
        if noof_rows <= self.info_list.calculate_noof_visible_items(0):
            current_index = 0
        self.info_list.on_scroll(current_index, silent=True)
        self.info_list.recreate_scrollbar()
        self.info_list.scrollbar.set_scroll(current_index)

    def add_category(self, name, info_list, is_expanded=True):
        category_row = CategoryListItem(name, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR])
        category_row.center_text = False
        rows = []
        unowned_rows = []
        for info in info_list:
            row = OwnableItemBase(info, self.manager.dlc_manager)
            row.selectable_row = False
            row.font = medium_standard_ui_font if self.info_list.normal_row_height >= 30 else small_standard_ui_font
            row.center_text = False
            if not row.owned:
                unowned_rows.append(row)
            rows.append(row)

        self.always_show_owned_rows = False
        if len(unowned_rows) > 0 and not self.always_show_owned_rows:
            self.info_list.add_list_item(category_row, unowned_rows)
        else:
            self.info_list.add_list_item(category_row, rows)
        if not is_expanded:
            category_row.on_expand(silent=True)
        return category_row
