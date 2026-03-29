from pyglet.gl import *
from pyglet.window import key
from aoslib.scenes import MenuScene
from aoslib.scenes.main.gameClass import GameClass
from aoslib.scenes.main.ugcObjectivesListPanel import UGCObjectivesListPanel
from aoslib.text import title_font, class_name_font, class_description_font, class_loadout_description_font, class_loadout_title_font, split_text_to_fit_screen, EDO_FONT, draw_text_with_size_validation, class_prefab_cost_font, draw_text_within_boundaries, medium_edo_ui_font, medium_aldo_ui_font, draw_text_with_alignment_and_size_validation, draw_text_lines, get_resized_font_and_formatted_text_to_fit_boundaries, medium_standard_ui_font
from aoslib.gui import TextButton, KeyDisplay, create_large_navbar, NAVBAR_LEFT, Label, HorizontalScrollBar, CustomButton
from aoslib.images import global_images
from aoslib.weapons.list import *
from aoslib.weapons import TOOL_IMAGES
from aoslib.scenes.gui.gridSelection import GridSelection
from aoslib.common import collides
from shared.constants import *
from shared.hud_constants import *
from shared.constants_prefabs import A3055, A3058, A3053, A3054, A3059
from shared.constants_ugc_objectives import UGC_OBJECTIVES_TYPES
from aoslib.scenes.main.gameScene import GameScene
from shared.prefabManager import PrefabManager
import aoslib.config, time
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.hud.hud import ViewGameStats
from aoslib.draw import draw_quad
import re

def get_tab_xywh(index, unselected_image=None, selected_image=None, current_index=None):
    pad_x = 4.25
    edge_x = 56
    image, other_image = (selected_image, unselected_image) if index == current_index else (unselected_image, selected_image)
    width = image.width if image is not None else 110
    height = image.height if image is not None else 37
    pos_x = edge_x + (index + 1) * pad_x + index * width + width * 0.5
    pos_y = 485 + (3 if current_index != index else 0)
    return (
     pos_x, pos_y, width, height)


def sort_prefabs_by_tag(prefabs, tags):
    prefabs_by_tag = {}
    for prefab in prefabs:
        for tag in [t for t in tags if t in A3058[prefab]]:
            prefabs_by_tag[tag] = prefabs_by_tag.get(tag, []) + [prefab]

    return prefabs_by_tag


def sort_ugc_tools_by_tag(ugc_tools, tags):
    ugc_tools_by_tag = {}
    for tag in tags:
        for ugc_tool in [tool for tool in ugc_tools if tool in UGC_ITEMS_BY_CATEGORY.get(tag, [])]:
            ugc_tools_by_tag[tag] = ugc_tools_by_tag.get(tag, []) + [ugc_tool]

    return ugc_tools_by_tag


def get_unique_selected_item_ids(tables):
    selected_items = []
    for table_index, table in enumerate(tables):
        for item in table.get_selected_item_ids_and_indices():
            selected_item = {'table_index': table_index, 'item_id': (item['id']), 'item_index': (item['index'])}
            if selected_item not in selected_items:
                selected_items.append(selected_item)

    return selected_items


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]


TAB_FONT, TAB_TEXT_LINES = xrange(2)

class SelectUGC(MenuScene):
    previous_menu = None
    current_tab_index = None
    tabs = []
    tabs_text_info = []
    prefabs_by_tag = {}
    ugc_items_by_tag = {}
    ugc_tables = []
    objectives_panel = None
    image_offset = [0.0, 0.0]
    selected_image_offset = [0.0, 0.0]
    tooltip_font = None
    tooltip_lines = []
    first_tab_index = 0

    def create_tabs(self, first_tab_index=0):
        self.first_tab_index = first_tab_index
        if len(self.tabs) > 0:
            self.on_tab_selected(0)
        del self.tabs_text_info[:]
        for index, tab in enumerate(self.tabs):
            tab_x, tab_y, tab_w, tab_h = get_tab_xywh(index, tab.unselected_image, tab.selected_image, self.current_tab_index)
            tab_w -= UI_CONTROL_SPACING * 2
            font, text_lines = get_resized_font_and_formatted_text_to_fit_boundaries(tab.text, tab_w, tab_h, medium_edo_ui_font, 2)
            self.tabs_text_info.append([font, text_lines])

    def on_start(self, menu=None, previous_menu=None):
        self.elements = []
        self.previous_menu = previous_menu
        x = 100
        y = 450
        self.opened = False
        if self.in_game_menu:
            self.back_button = TextButton(strings.BACK, 338, 79, 125, 45)
            self.back_button.add_handler(self.on_back_button_pressed, 0)
            self.elements.append(self.back_button)
            width = global_images.in_game_class_frame.width - SELECT_UGC_FRAME_WIDTH_DIFF
            self.button_background_x = self.back_button.x - self.back_button.width * 0.5 + width * 0.5
            self.button_background_y = self.back_button.y - self.back_button.height * 0.5 + BUTTON_BACKGROUND_Y_DIFF
            self.button_background_scale_x = float(width) / global_images.ugc_select_bg.width
            self.button_background_scale_y = float(self.back_button.height + 14) / global_images.ugc_select_bg.height
        else:
            self.navigation_bar = create_large_navbar()
            self.navigation_bar.add_handler(self.on_navigation)
            self.elements.append(self.navigation_bar)
            if not self.media.is_playing_music(SECONDARY_MENU_MUSIC1):
                self.media.stop_music()
                self.media.play_music(SECONDARY_MENU_MUSIC1, self.config.music_volume, fade_speed_when_finished=1 / SECONDARY_MUSIC_BED_FADE_TIME)
        self.objectives_panel = UGCObjectivesListPanel(self.manager, 414, 503, 325, 321)
        available_class_ids = []
        for id in self.manager.game_scene.selected_team.class_list:
            if id in self.manager.disabled_classes:
                contine
            available_class_ids.append(id)

        if len(available_class_ids) == 0:
            available_class_ids.append(DEFAULT_CLASS)
        self.game_classes = {}
        self.current_class_id = None
        for id in available_class_ids:
            self.game_classes[id] = GameClass(self.manager, id, self.manager.disabled_tools, self.manager.movement_speed_multipliers[id], self.config, self.manager.enable_fall_on_water_damage)
            if self.current_class_id is None:
                self.current_class_id = id
            if self.current_class_id is not None:
                player = self.manager.game_scene.player
                if self.in_game_menu and player is not None and player.current_class is not None:
                    if player.current_class.id == id:
                        self.game_classes[id].prefabs = player.current_class.prefabs
                        self.game_classes[id].ugc_tools = player.current_class.ugc_tools

        selected_items = self.game_classes[self.current_class_id].prefabs + self.game_classes[self.current_class_id].ugc_tools
        scene = self.manager.game_scene
        prefab_manager = scene.prefab_manager
        map_prefabs = prefab_manager.map_prefabs
        prefabs = [prefab for prefab in map_prefabs if prefab in A3058]
        tags = []
        for prefab in prefabs:
            for tag in A3058[prefab]:
                if tag not in tags and tag in A3053 and tag in A3054:
                    tags.append(tag)

        self.prefabs_by_tag = sort_prefabs_by_tag(prefabs, tags)
        ugc_tools = []
        for objective_id in scene.ugc_objectives.iterkeys():
            objective_type = UGC_OBJECTIVES_TYPES.get(objective_id, {})
            objective_ugc_tools = objective_type.get('entity_ids', [])
            ugc_tools += [tool for tool in objective_ugc_tools if tool not in ugc_tools]

        self.ugc_items_by_tag = sort_ugc_tools_by_tag(ugc_tools, UGC_ITEMS_BY_CATEGORY.keys())
        self.create_tables(prefab_manager, selected_items)
        self.tabs = []
        self.current_tab_index = None
        self.create_tabs()
        for button in self.inventory_buttons:
            if button not in self.elements:
                self.elements.append(button)

        self.selected_prefabs_frame_x = SELECT_UGC_PREFABS_FRAME_WIDTH
        self.tooltip_frame_width = global_images.prefab_selection_blueprint.width - UI_CONTROL_SPACING * 2 - SELECT_UGC_TOOLTIP_FRAME_X_PAD
        self.tooltip_frame_height = SELECT_UGC_TOOLTIP_FRAME_HEIGHT
        self.tooltip_frame_x = self.selected_prefabs_frame_x - global_images.prefab_selection_blueprint.width * 0.5 + SELECT_UGC_TOOLTIP_FRAME_X_PAD - 3
        self.tooltip_font, self.tooltip_lines = get_resized_font_and_formatted_text_to_fit_boundaries(strings.UGC_BACKPACK_HINT, self.tooltip_frame_width, self.tooltip_frame_height, medium_standard_ui_font, 2)
        self.select_button = TextButton(strings.SELECT, 422, 163, 310, 60)
        self.select_button.add_handler(self.on_select_button_pressed, 0)
        self.elements.append(self.select_button)
        return

    def create_tables(self, prefab_manager, selected_items=[]):
        self.ugc_tables = []
        for tag, prefabs in iter(sorted(self.prefabs_by_tag.items())):
            table_items = []
            for prefab in prefabs:
                image = prefab_manager.get_prefab_image(prefab)
                prefab_name = prefab_manager.get_prefab_string(prefab)
                size_label = strings.UGC_PREFAB_SIZE
                cost = prefab_manager.get_prefab_block_count(prefab_manager.get_prefab_id_by_name(prefab))
                size = strings.get_by_id(A3053[A3059(prefab, cost)])
                labels = []
                labels.append(Label(prefab_name, font=medium_edo_ui_font, x=5, y=-20, width=76, height=24, anchor_x='center', anchor_y='center'))
                labels.append(Label(size_label, font=medium_edo_ui_font, italic=True, x=4, y=-130, width=32, height=30, anchor_x='center', anchor_y='center'))
                labels.append(Label(size, font=medium_aldo_ui_font, bold=True, x=41, y=-127, width=37, height=24, anchor_x='center', anchor_y='center'))
                table_items.append((prefab_name, (prefab, image, labels)))

            sorted_table_items = [item for name, item in sorted(table_items, key=(lambda key: natural_sort_key(key[0])))]
            self.ugc_tables.append(GridSelection(sorted_table_items, 60, 461, UGC_MAX_LOADOUT_PREFABS, 0, 0.3, 86, 134, global_images.pf_blueprint_bg_default, global_images.pf_select_marker, 7, 14, selected_items, pad_x=7, image_offset=self.image_offset))

        for category, ugc_tools in self.ugc_items_by_tag.iteritems():
            table_items = []
            for ugc_tool in [tool for tool in ugc_tools if tool in UGCTOOL_LISTS[CLASS_UGCTOOLS_UGCBUILDER]]:
                image = global_images.ugc_tool_images[ugc_tool]
                ugc_tool_name = strings.get_by_id(UGC_ITEM_TO_STRING_ID[ugc_tool])
                labels = []
                labels.append(Label(ugc_tool_name, font=medium_edo_ui_font, x=8, y=-24, width=88, height=24, anchor_x='center', anchor_y='center'))
                table_items.append((ugc_tool_name, (ugc_tool, image, labels)))

            sorted_table_items = [item for name, item in sorted(table_items, key=(lambda key: natural_sort_key(key[0])))]
            self.ugc_tables.append(GridSelection(sorted_table_items, 60, 460, UGC_MAX_LOADOUT_PREFABS, 0, 0.3, 107, 133, global_images.gdata_blueprint_bg_default, global_images.gd_select_marker, 3, 6, selected_items, pad_x=7, image_offset=self.image_offset))

        for index, table in enumerate(self.ugc_tables):
            table.set_visible(False)
            table.set_enabled(False)
            table.add_on_item_clicked_handler(self.on_item_clicked, index)
            self.elements.append(table)

        self.create_loadout_buttons()
        selected_items = get_unique_selected_item_ids(self.ugc_tables)
        self.inventory_items = selected_items[:]
        self.update_loadout_buttons()

    def create_loadout_buttons(self):
        pad_x = 23.5
        first_x = 98
        width = height = 32
        pos_y = 138
        if hasattr(self, 'inventory_buttons'):
            for button in self.inventory_buttons:
                if button in self.elements:
                    self.elements.remove(button)

        self.inventory_buttons = []
        for index in xrange(UGC_MAX_LOADOUT_PREFABS):
            pos_x = first_x + (index + 1) * pad_x + index * width + width * 0.5
            button = CustomButton(pos_x, pos_y, width, height, image_offset=self.selected_image_offset)
            button.add_handler(self.on_loadout_button_pressed, index)
            button.set_enabled(False)
            self.elements.append(button)
            self.inventory_buttons.append(button)

    def update_loadout_buttons(self):
        scene = self.manager.game_scene
        prefab_manager = scene.prefab_manager
        count = 0
        for index, item in enumerate(self.inventory_items):
            if item['item_id'] in prefab_manager.map_prefabs:
                image = prefab_manager.get_prefab_image(item['item_id'])
            elif item['item_id'] in UGCTOOL_LISTS[CLASS_UGCTOOLS_UGCBUILDER]:
                image = global_images.ugc_tool_images[item['item_id']]
            else:
                image = None
            if image is None:
                continue
            self.inventory_buttons[count].image = image
            self.inventory_buttons[count].image_scale = min((self.inventory_buttons[count].width / float(image.width), self.inventory_buttons[count].height / float(image.height)))
            self.inventory_buttons[count].set_enabled(True)
            count += 1

        for index in xrange(UGC_MAX_LOADOUT_PREFABS - count):
            self.inventory_buttons[index + count].set_enabled(False)
            self.inventory_buttons[index + count].image = None

        return

    def on_loadout_button_pressed(self, value):
        self.remove_inventory_item(value)
        self.update_loadout_buttons()

    def remove_inventory_item(self, inventory_index):
        if inventory_index < 0 or inventory_index >= len(self.inventory_items):
            return
        first_item = self.inventory_items[inventory_index]
        table = self.ugc_tables[first_item['table_index']]
        table.on_scroll_list_item_deleted(first_item['item_index'])
        del self.inventory_items[inventory_index]

    def add_inventory_item(self, tab_index, item_id, item_index):
        self.inventory_items.append({'table_index': (tab_index + self.first_tab_index), 'item_id': item_id, 'item_index': item_index})

    def on_item_clicked(self, index, button_info):
        item_id = button_info['id']
        button_index = button_info['index']
        is_button_selected = item_id in self.ugc_tables[index].get_selected_item_ids()
        if is_button_selected:
            if len(self.inventory_items) >= UGC_MAX_LOADOUT_PREFABS:
                self.remove_inventory_item(0)
            self.add_inventory_item(self.current_tab_index, item_id, button_index)
        else:
            for index, item in enumerate(self.inventory_items):
                if item['item_id'] == item_id:
                    self.remove_inventory_item(index)
                    break

        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.update_loadout_buttons()

    def on_mouse_press(self, x, y, button, modifiers):
        for index, tab in enumerate(self.tabs):
            tab_x, tab_y, tab_w, tab_h = get_tab_xywh(index, tab.unselected_image, tab.selected_image, current_index=self.current_tab_index)
            half_w = tab_w * 0.5
            half_h = tab_h * 0.5
            x1 = tab_x - half_w
            x2 = tab_x + half_w
            y1 = tab_y - half_h
            y2 = tab_y + half_h
            if collides(x1, y1, x2, y2, x, y, x, y):
                self.on_tab_selected(index)
                return

        super(SelectUGC, self).on_mouse_press(x, y, button, modifiers)

    def on_tab_selected(self, index):
        previous_tab_index = self.current_tab_index
        self.current_tab_index = index
        if self.current_tab_index != previous_tab_index:
            previous_table_index = self.tabs[previous_tab_index].table_index if previous_tab_index is not None else None
            current_table_index = self.tabs[self.current_tab_index].table_index if self.current_tab_index is not None else None
            for table_index, table in enumerate(self.ugc_tables):
                if current_table_index != table_index:
                    self.ugc_tables[table_index].set_visible(False)
                    self.ugc_tables[table_index].set_enabled(False)
                else:
                    self.ugc_tables[table_index].set_visible(True)
                    self.ugc_tables[table_index].set_enabled(True)

            current_scrollbar = self.ugc_tables[current_table_index].scrollbar if current_table_index is not None else None
            previous_scrollbar = self.ugc_tables[previous_table_index].scrollbar if previous_table_index is not None else None
            if current_scrollbar != previous_scrollbar:
                if previous_scrollbar:
                    self.elements.remove(previous_scrollbar)
                if current_scrollbar:
                    self.elements.append(current_scrollbar)
            if current_table_index >= len(self.prefabs_by_tag.keys()) and self.objectives_panel not in self.elements:
                self.elements.append(self.objectives_panel)
            elif current_table_index < len(self.prefabs_by_tag.keys()) and self.objectives_panel in self.elements:
                self.elements.remove(self.objectives_panel)
        return

    def on_stop(self):
        super(SelectUGC, self).on_stop()

    def on_scroll(self, value, silent=False):
        if not silent:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)

    def on_back_button_pressed(self, value):
        if self.previous_menu is None:
            from aoslib.scenes.main.gameScene import GameScene
            self.set_scene(GameScene)
        else:
            self.parent.set_menu(self.previous_menu, back=True)
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        return

    def on_select_button_pressed(self, value):
        scene = self.manager.game_scene
        self.create_loadout_list()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if self.in_game_menu:
            if scene.player and scene.player.team and scene.player.team.id == TEAM_SPECTATOR:
                scene.create_player(self.game_classes[self.current_class_id])
            else:
                scene.class_changed(self.game_classes[self.current_class_id])
        else:
            scene.create_player(self.game_classes[self.current_class_id])
            self.media.stop_music()
        if scene.game_statistics_active:
            self.manager.set_menu(ViewGameStats)
        else:
            self.set_scene(GameScene)

    def on_navigation(self, button_id):
        self.media.stop_music()
        if button_id is NAVBAR_LEFT:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            scene = self.manager.game_scene
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            self.parent.set_menu(LoadingMenu, back=True, from_server_menu=False)
        else:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            self.manager.set_main_menu()

    def on_key_press(self, symbol, modifiers, exit_menu_key=None):
        if exit_menu_key is None:
            exit_menu_key = self.config.change_class
        super(SelectUGC, self).on_key_press(symbol, modifiers)
        if symbol == key.RETURN or symbol == key.ENTER:
            self.on_select_button_pressed(0)
            return
        else:
            if self.in_game_menu:
                config = self.config
                if symbol != exit_menu_key and symbol != self.config.menu:
                    return
                from aoslib.scenes.main.gameScene import GameScene
                self.set_scene(GameScene)
                self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            return

    def create_loadout_list(self):
        loadout = []
        prefabs = []
        ugc_tools = []
        add_flareblock = False
        for index in range(CLASS_NOOF_SELECTABLE_ITEMS) + [CLASS_UGC_TOOLS]:
            default_items = CLASS_ITEMS[self.current_class_id][index]
            for item in default_items:
                if item == FLAREBLOCK_TOOL:
                    continue
                if index == CLASS_PREFABS:
                    prefabs_only = []
                    for selected_item in self.inventory_items:
                        if selected_item['item_id'] in self.manager.game_scene.prefab_manager.map_prefabs:
                            prefabs_only.append(selected_item['item_id'])

                    for prefab in prefabs_only:
                        if prefab not in prefabs:
                            prefabs.append(prefab)

                elif index == CLASS_UGC_TOOLS:
                    ugc_tools_only = []
                    for selected_item in self.inventory_items:
                        if selected_item['item_id'] in UGCTOOL_LISTS[item]:
                            ugc_tools_only.append(selected_item['item_id'])

                    for tool in ugc_tools_only:
                        if tool not in ugc_tools:
                            ugc_tools.append(tool)

                else:
                    loadout.append(item)

        self.game_classes[self.current_class_id].set_common_loadout_items(loadout, add_flareblock)
        self.game_classes[self.current_class_id].loadout = loadout
        self.game_classes[self.current_class_id].prefabs = prefabs
        self.game_classes[self.current_class_id].ugc_tools = ugc_tools
        setattr(self.config, aoslib.config.loadout_name(self.current_class_id), self.game_classes[self.current_class_id].loadout)
        if len(self.game_classes[self.current_class_id].prefabs) > 0:
            setattr(self.config, aoslib.config.prefab_name(self.current_class_id), self.game_classes[self.current_class_id].prefabs)
        self.config.save()
        scene = self.manager.game_scene
        if scene and scene.player and scene.player.character:
            ugc_tool = self.manager.game_scene.get_player_tool(UGC_TOOL)
            if ugc_tool:
                ugc_tool.reset_item_groups_and_indices()

    def draw_tabs(self):
        for index, tab in enumerate(self.tabs):
            tab_x, tab_y, tab_w, tab_h = get_tab_xywh(index, tab.unselected_image, tab.selected_image, self.current_tab_index)
            tab_half_w = tab_w * 0.5
            if index == self.current_tab_index:
                tab.selected_image.blit(tab_x, tab_y)
                tab_color = MENU_FONT_COLOR2
            else:
                tab.unselected_image.blit(tab_x, tab_y)
                tab_color = MENU_FONT_COLOR
            tab_x += UI_CONTROL_SPACING
            tab_w -= UI_CONTROL_SPACING * 2
            font = self.tabs_text_info[index][TAB_FONT] if self.tabs_text_info[index][TAB_FONT] is not None else medium_edo_ui_font
            draw_text_lines(self.tabs_text_info[index][TAB_TEXT_LINES], tab_x - tab_half_w, tab_y - tab_h * 0.5, tab_w, tab_h, font, 1, tab_color, 'center', 'center')

        return

    def draw_panel(self):
        pass

    def draw(self):
        scene = self.manager.game_scene
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = (400, 300)
        text_height = 50
        if self.in_game_menu:
            text_x = 220
            text_y = 515
            text_width = 360
            global_images.in_game_class_frame.blit(mid_x, mid_y - 10)
            draw_text_with_alignment_and_size_validation(self.title, text_x, text_y, text_width, text_height, MENU_FONT_COLOR, title_font, alignment_x='center', alignment_y='center')
            gl.glPushMatrix()
            gl.glTranslatef(mid_x, self.button_background_y, 0.0)
            gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 1.0)
            global_images.ugc_select_bg.blit(0, 0)
            gl.glPopMatrix()
        else:
            text_x = 120
            text_y = 530
            text_width = 560
            global_images.large_frame.blit(mid_x, mid_y)
            draw_text_with_alignment_and_size_validation(self.title, text_x, text_y, text_width, text_height, MENU_FONT_COLOR, title_font, alignment_x='center', alignment_y='center')
        self.draw_panel()
        self.draw_tabs()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        x = self.selected_prefabs_frame_x
        y = self.select_button.y - self.select_button.height * 0.5
        global_images.prefab_selection_blueprint.blit(x, y + BUTTON_BACKGROUND_Y_DIFF)
        draw_quad(self.tooltip_frame_x, y + UI_CONTROL_SPACING * 2, self.tooltip_frame_width, self.tooltip_frame_height, SELECT_UGC_TOOLTIP_FRAME_COLOUR)
        x = self.tooltip_frame_x + TEXT_BACKGROUND_SPACING
        width = self.tooltip_frame_width - TEXT_BACKGROUND_SPACING * 2
        draw_text_lines(self.tooltip_lines, x, y + UI_CONTROL_SPACING * 2, width, self.tooltip_frame_height, self.tooltip_font, 2, MENU_FONT_COLOR, 'center', 'center')
        global_images.ugc_select_bg.blit(self.select_button.x + self.select_button.width * 0.5, self.select_button.y - self.select_button.height * 0.5 + BUTTON_BACKGROUND_Y_DIFF)
        for element in self.elements:
            element.draw()
