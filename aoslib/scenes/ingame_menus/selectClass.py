from pyglet.gl import *
from pyglet.window import key
from aoslib.scenes import MenuScene
from aoslib.scenes.main.gameClass import GameClass
from aoslib.text import title_font, class_name_font, class_description_font, class_loadout_description_font, class_loadout_title_font, split_text_to_fit_screen, EDO_FONT, draw_text_with_size_validation, class_prefab_cost_font, draw_text_within_boundaries
from aoslib.gui import TextButton, KeyDisplay, create_large_navbar, NAVBAR_LEFT, Label, HorizontalScrollBar
from aoslib.images import global_images
from aoslib.weapons.list import *
from aoslib.weapons import TOOL_IMAGES
from aoslib.scenes.gui.horizontalListSelection import HorizontalListSelection, CLASS_SELECTION_HLIST4, CLASS_SELECTION_HLIST5, LOADOUT_HLIST
from aoslib.scenes.gui.tableSelection import TableSelection
from shared.constants import *
from shared.hud_constants import *
from aoslib.scenes.main.gameScene import GameScene
import aoslib.config, time
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.hud.hud import ViewGameStats
from shared.constants_DLC import is_tool_selectable

class SelectClass(MenuScene):
    title = strings.CHOOSE_CLASS
    game_classes = {}
    current_class_id = None
    class_item_ui_lists = {}
    in_game_menu = False
    loadout_hovered_item = {}
    class_hovered_item = {}
    opened = False
    class_vo = None
    previous_menu = None

    def on_start(self, menu=None, previous_menu=None):
        self.select_button = None
        self.is_loadout_valid = True
        self.elements = []
        self.previous_menu = previous_menu
        x = 105
        y = 455
        self.opened = False
        if self.in_game_menu:
            self.back_button = TextButton(strings.BACK, 338, 78, 125, 45)
            self.back_button.add_handler(self.on_back_button_pressed, 0)
            self.elements.append(self.back_button)
            width = global_images.in_game_class_frame.width - SELECT_CLASS_WIDTH_FRAME_DIFF
            self.button_background_x = self.back_button.x - self.back_button.width * 0.5 + width * 0.5
            self.button_background_y = self.back_button.y - self.back_button.height * 0.5 + 2
            self.button_background_scale_x = float(width) / global_images.ugc_select_bg.width
            self.button_background_scale_y = float(self.back_button.height + 14) / global_images.ugc_select_bg.height
        else:
            self.navigation_bar = create_large_navbar()
            self.navigation_bar.add_handler(self.on_navigation)
            self.elements.append(self.navigation_bar)
            if not self.media.is_playing_music(SECONDARY_MENU_MUSIC1):
                self.media.stop_music()
                self.media.play_music(SECONDARY_MENU_MUSIC1, self.config.music_volume, fade_speed_when_finished=1 / SECONDARY_MUSIC_BED_FADE_TIME)
        self.game_classes = {}
        self.current_class_id = None
        images = []
        scene = self.manager.game_scene
        self.team_id = self.manager.game_scene.selected_team.id
        if self.team_id is TEAM_SPECTATOR:
            from aoslib.scenes.main.gameScene import GameScene
            scene.create_player()
            self.set_scene(GameScene)
            scene.media.stop_music()
            return
        else:
            first_id = None
            available_class_ids = []
            for id in self.manager.game_scene.selected_team.class_list:
                if id in self.manager.disabled_classes:
                    continue
                available_class_ids.append(id)

            if len(available_class_ids) == 0:
                available_class_ids.append(DEFAULT_CLASS)
            for id in available_class_ids:
                self.game_classes[id] = GameClass(self.manager, id, self.manager.disabled_tools, self.manager.movement_speed_multipliers[id], self.config, self.manager.enable_fall_on_water_damage)
                if first_id is None:
                    first_id = id
                if self.current_class_id is None:
                    player = self.manager.game_scene.player
                    if self.in_game_menu and player is not None and player.current_class is not None:
                        if player.current_class.id == id:
                            self.game_classes[id].prefabs = player.current_class.prefabs
                            self.set_current_class(id)
                    else:
                        self.set_current_class(id)
                if self.game_classes[id].is_selectable():
                    images.append([id, global_images.class_icons[id][self.team_id]])
                else:
                    images.append([id, global_images.disabled_class_icons[id][self.team_id]])

            if self.current_class_id is None:
                self.current_class_id = first_id
            self.images = images
            if len(self.game_classes) > 4:
                self.classes_per_page = 5
                list_type = CLASS_SELECTION_HLIST5
                image_scale = 4.0 / 5.0
                self.class_display_interval = SELECT_CLASS_DISPLAY_INTERVAL_5
            else:
                self.classes_per_page = 4
                image_scale = 1.0
                list_type = CLASS_SELECTION_HLIST4
                self.class_display_interval = SELECT_CLASS_DISPLAY_INTERVAL_4
                self.class_scrollbar = None
            self.class_ui_selection = HorizontalListSelection(images, x + 122, y - 5, 1, image_scale, list_type, [self.current_class_id], False, False, scale_hover=0.22)
            self.class_ui_selection.add_on_item_clicked_handler(self.on_class_selected, 0)
            self.class_ui_selection.add_on_mouse_over_handler(self.on_mouse_over_class_button, 0)
            self.class_ui_selection.add_on_page_change_handler(self.on_page_change_class_selection, 0)
            self.key_displays = []
            half_button_size = SELECT_CLASS_KEY_DISPLAY_SIZE * 0.5
            for index, image in enumerate(self.images):
                key_x = SELECT_CLASS_KEYDISPLAY_X + self.class_display_interval * index + half_button_size
                if index >= len(global_images.key_images):
                    break
                key_display = KeyDisplay(key_x, SELECT_CLASS_KEYDISPLAY_Y, str(index + 1), size=SELECT_CLASS_KEY_DISPLAY_SIZE)
                key_display.add_handler(self.class_ui_selection.on_itemindex_selected, index)
                self.elements.append(key_display)
                self.key_displays.append(key_display)
                if index >= self.classes_per_page:
                    key_display.set_visible(False)

            self.elements.append(self.class_ui_selection)
            selected_items = self.game_classes[self.current_class_id].loadout
            self.class_item_ui_lists = {}
            x = 316
            y = 291
            for index in xrange(CLASS_NOOF_SELECTABLE_ITEMS):
                self.loadout_hovered_item[index] = None
                images = self.get_class_images(index)
                noof_selected_items = 1
                scale = 0.1
                if index == CLASS_PREFABS:
                    noof_selected_items = 3
                    scale = 0.15
                    selected_items = self.game_classes[self.current_class_id].prefabs
                    self.class_item_ui_lists[index] = TableSelection(images, x + 148, 287, noof_selected_items, 1, scale, 3, 12, selected_items, draw_frame=True)
                else:
                    self.class_item_ui_lists[index] = HorizontalListSelection(images, x, y, noof_selected_items, scale, LOADOUT_HLIST, selected_items, True)
                self.class_item_ui_lists[index].add_on_mouse_over_handler(self.on_mouse_over_loadout_button, index)
                self.class_item_ui_lists[index].add_on_page_change_handler(self.on_page_change_loudout_selection, index)
                self.class_item_ui_lists[index].add_on_item_clicked_handler(self.on_loadout_item_button_clicked, index)
                self.elements.append(self.class_item_ui_lists[index])
                y -= 53

            self.select_button = TextButton(strings.SELECT, 599, 139, 124, 40)
            self.select_button.add_handler(self.on_select_button_pressed, 0)
            self.elements.append(self.select_button)
            self.update_select_button()
            if len(self.game_classes) > 5:
                self.class_scrollbar = HorizontalScrollBar(SELECT_CLASS_SCROLLBAR_X, SELECT_CLASS_SCROLLBAR_Y, SELECT_CLASS_SCROLLBAR_WIDTH, SELECT_CLASS_SCROLLBAR_HEIGHT, len(self.game_classes), 5)
                self.elements.append(self.class_scrollbar)
                self.class_scrollbar.add_on_scrolled_handler(self.on_scroll)
                self.class_ui_selection.set_scrollbar(self.class_scrollbar)
            else:
                self.class_scrollbar = None
            class_index = self.get_index_of_class(self.current_class_id)
            self.class_ui_selection.on_itemindex_selected(class_index)
            self.opened = True
            self.popup_timer = None
            self.draw_popup_info = False
            return

    def get_index_of_class(self, class_id):
        for index, image in enumerate(self.images):
            id = image[0]
            if id == class_id:
                return index

        print('Could not find class')
        return 0

    def on_stop(self):
        super(MenuScene, self).on_stop()

    def on_scroll(self, value, silent=False):
        if not silent:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.class_ui_selection.on_scrollbar_scroll(value, silent=silent)

    def on_mouse_over_loadout_button(self, index, button_info):
        self.loadout_hovered_item[index] = button_info
        self.popup_timer = time.time()
        self.draw_popup_info = False

    def on_mouse_over_class_button(self, index, button_info):
        self.class_hovered_item[index] = button_info
        self.popup_timer = time.time()
        self.draw_popup_info = False

    def on_page_change_class_selection(self, id, min_index, max_index):
        key_x = SELECT_CLASS_KEYDISPLAY_X
        for index, key_display in enumerate(self.key_displays):
            if index >= min_index and index <= max_index:
                key_display.set_position(key_x, SELECT_CLASS_KEYDISPLAY_Y)
                key_display.set_visible(True)
                key_x += self.class_display_interval
            else:
                key_display.set_visible(False)

    def on_loadout_item_button_clicked(self, index, button_info):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.update_item_selection_validation()

    def on_page_change_loudout_selection(self, id, min_index, max_index):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.update_item_selection_validation()

    def get_class_images(self, index):
        images = []
        character_selectable = self.game_classes[self.current_class_id].is_selectable()
        if index is CLASS_PREFABS and self.current_class_id != CLASS_ZOMBIE and self.current_class_id != CLASS_CLASSIC_SOLDIER:
            if FLAREBLOCK_TOOL not in self.manager.disabled_tools:
                images.append([FLAREBLOCK_TOOL, TOOL_IMAGES[FLAREBLOCK_TOOL], character_selectable])
        for item in CLASS_ITEMS[self.game_classes[self.current_class_id].id][index]:
            if index is CLASS_PREFABS:
                if PREFAB_TOOL in self.manager.disabled_tools:
                    continue
                if item == MAP_PREFABS:
                    for name in self.manager.game_scene.prefab_manager.map_prefabs:
                        images.append([name, self.manager.game_scene.prefab_manager.get_prefab_image(name), character_selectable])

                else:
                    prefab_list = PREFAB_LISTS[item]
                    for prefab in prefab_list:
                        if not self.is_item_map_prefab(prefab):
                            images.append([prefab, self.manager.game_scene.prefab_manager.get_prefab_image(prefab), character_selectable])

            elif item in self.manager.disabled_tools:
                continue
            image = TOOL_IMAGES[item]
            tool_enabled = character_selectable and is_tool_selectable(item, self.manager.dlc_manager)
            if item == SNIPER_TOOL:
                image = image[self.team_id - TEAM1]
            images.append([item, image, tool_enabled])

        return images

    def is_item_map_prefab(self, item):
        for prefab in self.manager.game_scene.prefab_manager.map_prefabs:
            if prefab.lower() == item.lower():
                return True

        return False

    def on_back_button_pressed(self, value):
        if self.previous_menu is None:
            from aoslib.scenes.main.gameScene import GameScene
            self.set_scene(GameScene)
        else:
            self.parent.set_menu(self.previous_menu, back=True)
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        return

    def on_select_button_pressed(self, value):
        if not self.manager.game_scene.selected_team or self.manager.game_scene.selected_team.locked_class:
            return
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
        if button_id is NAVBAR_LEFT:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            scene = self.manager.game_scene
            if scene.force_team_join is None:
                from aoslib.scenes.ingame_menus.selectTeam import SelectTeam
                self.parent.set_menu(SelectTeam, back=True)
            else:
                from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
                self.parent.set_menu(LoadingMenu, back=True, from_server_menu=False)
        return

    def update_item_selection_validation(self):
        self.is_loadout_valid = self.is_item_selection_valid()

    def is_item_selection_valid(self):
        for index in xrange(CLASS_NOOF_SELECTABLE_ITEMS):
            selected_ids = self.class_item_ui_lists[index].get_selected_item_ids()
            for item in selected_ids:
                if index != CLASS_PREFABS:
                    if not is_tool_selectable(item, self.manager.dlc_manager):
                        return False

        return True

    def create_loadout_list(self):
        loadout = []
        prefabs = []
        add_flareblock = False
        for index in xrange(CLASS_NOOF_SELECTABLE_ITEMS):
            selected_ids = self.class_item_ui_lists[index].get_selected_item_ids()
            for item in selected_ids:
                if item == FLAREBLOCK_TOOL:
                    add_flareblock = True
                    continue
                if index == CLASS_PREFABS:
                    prefabs.append(item)
                else:
                    loadout.append(item)

        self.game_classes[self.current_class_id].set_common_loadout_items(loadout, add_flareblock)
        self.game_classes[self.current_class_id].loadout = loadout
        self.game_classes[self.current_class_id].prefabs = prefabs
        setattr(self.config, aoslib.config.loadout_name(self.current_class_id), self.game_classes[self.current_class_id].loadout)
        if len(self.game_classes[self.current_class_id].prefabs) > 0:
            setattr(self.config, aoslib.config.prefab_name(self.current_class_id), self.game_classes[self.current_class_id].prefabs)
        self.config.save()

    def on_class_selected(self, index, button_info):
        if self.opened:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.create_loadout_list()
        old_class_id = self.current_class_id
        self.set_current_class(button_info['id'])
        button_value = button_info['id']
        if self.in_game_menu:
            button_value += 1
        count = 0
        for index in xrange(CLASS_NOOF_SELECTABLE_ITEMS):
            images = self.get_class_images(index)
            if index == CLASS_PREFABS:
                selected_items = self.game_classes[self.current_class_id].prefabs
            else:
                selected_items = self.game_classes[self.current_class_id].loadout
            self.class_item_ui_lists[index].populate_items_list(images, selected_items)

        self.loadout_hovered_item = {}
        self.class_hovered_item = {}
        self.draw_popup_info = False
        self.update_item_selection_validation()

    def on_key_press(self, symbol, modifiers):
        super(SelectClass, self).on_key_press(symbol, modifiers)
        if symbol == key.RETURN or symbol == key.ENTER:
            self.on_select_button_pressed(0)
            return
        if self.in_game_menu:
            config = self.config
            if symbol != config.change_class and symbol != self.config.menu:
                return
            from aoslib.scenes.main.gameScene import GameScene
            self.set_scene(GameScene)
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)

    def draw_prefab_info(self, button, x, y, prefab_id):
        x -= 25
        y -= 30
        glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.prefab_info_frame.blit(x, y)
        image_x = x
        image_y = y + 44
        if prefab_id == FLAREBLOCK_TOOL:
            image_scale = 0.35
        else:
            image_scale = 0.5
        gl.glPushMatrix()
        gl.glTranslatef(image_x, image_y, 0.0)
        gl.glScalef(image_scale, image_scale, 1.0)
        button.image.blit(0, 0)
        gl.glPopMatrix()
        if prefab_id == FLAREBLOCK_TOOL:
            name = strings.get_by_id(TOOL_NAMES[prefab_id])
            cost = str(FLAREBLOCK_COST)
        else:
            name = strings.get_by_id(prefab_id.upper())
            id = self.manager.game_scene.prefab_manager.get_prefab_id_by_name(prefab_id)
            cost = self.manager.game_scene.prefab_manager.get_prefab_block_count(id)
        text_x = x - 80
        text_y = y - 55
        description_x = text_x
        description_y = text_y - 45
        cost_x = text_x + 118
        cost_y = text_y - 45
        width = global_images.prefab_info_frame.width - 40.0
        draw_text_with_size_validation(name, text_x, text_y, width, 20, MENU_FONT_COLOR, class_loadout_title_font)
        width = 110
        height = 40
        text = strings.BLOCK_USAGE
        if class_prefab_cost_font.get_content_width(text) > width:
            draw_text_within_boundaries(text, description_x, description_y + height * 0.5, width, height, class_prefab_cost_font, 5, MENU_FONT_COLOR, alignment='center')
        else:
            class_prefab_cost_font.draw(text, description_x, description_y + height * 0.25, MENU_FONT_COLOR)
        draw_text_with_size_validation(str(cost), cost_x, cost_y, 30, 30, MENU_FONT_COLOR, class_prefab_cost_font)

    def draw_weapon_info(self, button, x, y, tool_id):
        glColor4f(1.0, 1.0, 1.0, 1.0)
        image_scale = 0.35
        load_info_frame = None
        tool_selectable = is_tool_selectable(tool_id, self.manager.dlc_manager)
        if tool_selectable:
            load_info_frame = global_images.loadout_info_frame
            tool_disabled_offset = 0
        else:
            load_info_frame = global_images.disabled_loadout_info_frame
            tool_disabled_offset = 100
        load_info_frame.blit(x, y)
        image_x = x + 1
        image_y = y + 77 - tool_disabled_offset * image_scale
        gl.glPushMatrix()
        gl.glTranslatef(image_x, image_y, 0.0)
        gl.glScalef(image_scale, image_scale, 1.0)
        button.image.blit(0, 0)
        gl.glPopMatrix()
        if not tool_selectable:
            text_x = x - 100
            dlc_text_y = 417
            description = strings.DLC_NOT_PURCHASHED
            description = split_text_to_fit_screen(class_loadout_description_font, description, load_info_frame.width, 60)
            dlc_descriptions = description.split('\n')
            for description in dlc_descriptions:
                class_loadout_description_font.draw(description, text_x, dlc_text_y, MENU_FONT_COLOR)
                dlc_text_y -= class_loadout_description_font.get_line_height()

        text_x = x - 105
        text_y = image_y - 100
        text = strings.get_by_id(TOOL_NAMES[tool_id])
        width = load_info_frame.width - 40.0
        height = 20.0
        draw_text_with_size_validation(text, text_x, text_y, width, height, MENU_FONT_COLOR, class_loadout_title_font)
        tool_descriptions = strings.get_by_id(TOOL_DESCRIPTIONS[tool_id]).split('\n')
        text_y -= 19
        negative_text_y = text_y - 65
        positive_description = True
        for description in tool_descriptions:
            if description.startswith('- ') and positive_description == True:
                text_y = negative_text_y
                positive_description = False
            description = description.replace('+ ', '').replace('- ', '')
            description_lines = split_text_to_fit_screen(class_loadout_description_font, description, load_info_frame.width - 20, 60)
            description_lines = description_lines.split('\n')
            text_x = x - 50
            line_count = 0
            for line in description_lines:
                line_count += 1
                line = line.replace(u'\u2022', ' ')
                draw_text_with_size_validation(line, text_x, text_y, load_info_frame.width - 90, 20, MENU_FONT_COLOR, class_loadout_description_font, center_text=False)
                text_y -= class_loadout_description_font.get_line_height() - 2

            if line_count > 1:
                text_y -= 3
            else:
                text_y -= 5

        return

    def draw_loadout_info(self):
        for id, item in self.loadout_hovered_item.iteritems():
            if item is None:
                continue
            button = item['button']
            if button is None or button.image is None:
                continue
            x = button.x + button.width + global_images.loadout_info_frame.width * 0.5 + 7
            y = 252
            arrow_x = button.x + button.width
            arrow_y = button.y - button.height * 0.5
            if id == CLASS_PREFABS:
                arrow_x -= 9
                self.draw_prefab_info(button, x, y, item['id'])
            else:
                self.draw_weapon_info(button, x, y, item['id'])
            if is_tool_selectable(item['id'], self.manager.dlc_manager):
                global_images.class_frame_arrow.blit(arrow_x, arrow_y)
            else:
                global_images.disabled_class_frame_arrow.blit(arrow_x, arrow_y)

        return

    def draw_class_info(self):
        for id, item in self.class_hovered_item.iteritems():
            if item is None:
                continue
            button = item['button']
            character_selectable = self.game_classes[item['id']].is_selectable()
            info_frame_left = None
            info_frame_right = None
            info_frame_y_offset = 0
            if character_selectable:
                info_frame_left = global_images.class_info_frame_left
                info_frame_right = global_images.class_info_frame_right
            else:
                info_frame_left = global_images.disabled_class_info_frame_left
                info_frame_right = global_images.disabled_class_info_frame_right
                info_frame_y_offset = -16
            if self.classes_per_page == 4:
                tip_offset_x = SELECT_CLASS_TOOLTIP_OFFSET_X4
            else:
                tip_offset_x = SELECT_CLASS_TOOLTIP_OFFSET_X5
            if button.x >= MENU_WINDOW_WIDTH / 2:
                x = button.x - info_frame_left.width + button.width + tip_offset_x
            else:
                x = button.x + info_frame_right.width - tip_offset_x
            y = button.y - float(button.text_height) / 2.0 + 15 + info_frame_y_offset
            glColor4f(1.0, 1.0, 1.0, 1.0)
            gl.glPushMatrix()
            gl.glTranslatef(x, y, 0.0)
            if button.x >= MENU_WINDOW_WIDTH / 2:
                info_frame_right.blit(0, 0)
            else:
                info_frame_left.blit(0, 0)
            gl.glPopMatrix()
            y -= info_frame_y_offset
            if button.x >= MENU_WINDOW_WIDTH / 2:
                text_x = x - 10
            else:
                text_x = x
            text_x -= 130.0
            text_y = y + 52
            if not character_selectable:
                description = strings.DLC_NOT_PURCHASHED
                description = split_text_to_fit_screen(class_loadout_description_font, description, info_frame_left.width, 60)
                tool_descriptions = description.split('\n')
                if button.x >= MENU_WINDOW_WIDTH / 2:
                    text_x = x - 135
                else:
                    text_x = x - 115
                y += 10
                for description in tool_descriptions:
                    class_loadout_description_font.draw(description, text_x, y + 20, MENU_FONT_COLOR)
                    y -= class_loadout_description_font.get_line_height()

                y -= 20
            draw_text_with_size_validation(strings.get_by_id(CLASS_NAMES[item['id']]), text_x, text_y, info_frame_left.width - 60, 28.0, MENU_FONT_COLOR, class_name_font)
            description = strings.get_by_id(CLASS_DESCRIPTIONS[item['id']])
            description = split_text_to_fit_screen(class_loadout_description_font, description, info_frame_left.width, 60)
            tool_descriptions = description.split('\n')
            if button.x >= MENU_WINDOW_WIDTH / 2:
                text_x = x - 135
            else:
                text_x = x - 115
            y += 10
            for description in tool_descriptions:
                class_loadout_description_font.draw(description, text_x, y + 20, MENU_FONT_COLOR)
                y -= class_loadout_description_font.get_line_height()

            text_x += 10
            y += 10
            gl.glPushMatrix()
            gl.glTranslatef(text_x, y + 5, 0.0)
            gl.glScalef(0.1, 0.1, 1.0)
            TOOL_IMAGES[BLOCK_TOOL].blit(0, 0)
            gl.glPopMatrix()
            initial_block_count = int(CLASS_BLOCKS[item['id']][0] * self.manager.block_wallet_multiplier)
            max_block_count = int(CLASS_BLOCKS[item['id']][1] * self.manager.block_wallet_multiplier)
            description = strings.BLOCKS + ': ' + str(initial_block_count) + ' / ' + str(max_block_count)
            class_loadout_description_font.draw(description, text_x + 20, y, MENU_FONT_COLOR)

        return

    def draw(self):
        if self.team_id is TEAM_SPECTATOR:
            return
        scene = self.manager.game_scene
        self.select_button.set_enabled(self.manager.game_scene.selected_team and not self.manager.game_scene.selected_team.locked_class and self.game_classes[self.current_class_id].is_selectable() and self.is_loadout_valid)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = (400, 300)
        if self.in_game_menu:
            global_images.in_game_class_frame.blit(mid_x, mid_y - 10)
            title_font.draw(self.title.upper(), mid_x, mid_y + 220, MENU_FONT_COLOR, center=True)
            gl.glPushMatrix()
            gl.glTranslatef(mid_x, self.button_background_y, 0.0)
            gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 1.0)
            global_images.ugc_select_bg.blit(0, 0)
            gl.glPopMatrix()
        else:
            global_images.large_frame.blit(mid_x, mid_y)
            title_font.draw(self.title.upper(), mid_x, mid_y + 240, MENU_FONT_COLOR, center=True)
        if self.classes_per_page == 4:
            global_images.class_background_frame.blit(mid_x, mid_y)
        else:
            global_images.class_background_frame5.blit(mid_x, mid_y)
        if self.game_classes[self.current_class_id].is_selectable():
            global_images.class_images[self.current_class_id][self.team_id].blit(mid_x + 260, 224)
        else:
            global_images.disabled_class_images[self.current_class_id][self.team_id].blit(mid_x + 260, 224)
        for element in self.elements:
            element.draw()

        description_x = 84
        description_y = 270
        for id, item in self.class_item_ui_lists.items():
            if id == CLASS_PREFABS:
                constructs_text = strings.get_by_id(CLASS_ITEMS_NAME[id])
                draw_text_with_size_validation(constructs_text, mid_x + 70, mid_y - 11, 114, 20, MENU_FONT_COLOR, class_description_font)
            else:
                height = item._buttons[0].height
                width = 80
                text_y = item._buttons[0].y - height + 4
                text = strings.get_by_id(CLASS_ITEMS_NAME[id])
                if len(text.split(' ')) == 1:
                    draw_text_with_size_validation(text, description_x, text_y, width, height, MENU_FONT_COLOR, class_description_font)
                else:
                    draw_text_within_boundaries(text, description_x, text_y + height * 0.5, width, height, class_description_font, 5, MENU_FONT_COLOR, alignment='center')

        x = SELECT_CLASS_NAMEDISPLAY_X if self.classes_per_page == 4 else SELECT_CLASS_NAMEDISPLAY_X5
        y = SELECT_CLASS_NAMEDISPLAY_Y
        min_index = self.class_ui_selection.get_min_index()
        max_index = min(min_index + self.classes_per_page, len(self.game_classes))
        for image_index in xrange(min_index, max_index):
            id = self.images[image_index][0]
            color = MENU_FONT_COLOR
            if id == self.current_class_id:
                color = MENU_FONT_COLOR2
            available_width = 440 / self.classes_per_page
            draw_text_with_size_validation(self.game_classes[id].name, x, y, available_width, 25, color, class_name_font)
            x += self.class_display_interval

        if self.draw_popup_info:
            self.draw_loadout_info()
            self.draw_class_info()

    def update(self, dt):
        if self.popup_timer is not None:
            delta = time.time() - self.popup_timer
            if delta > 0.5:
                self.popup_timer = None
                self.draw_popup_info = True
        if self.draw_popup_info == True and self.is_mouse_on_item() == False:
            self.draw_popup_info = False
        scene = self.manager.game_scene
        if scene.game_statistics_active:
            self.manager.set_menu(ViewGameStats)
        return

    def is_mouse_on_item(self):
        for key, value in self.loadout_hovered_item.iteritems():
            if value is not None:
                return True

        for key, value in self.class_hovered_item.iteritems():
            if value is not None:
                return True

        return False

    def packet_received(self, packet, sent_time):
        pass

    def set_current_class(self, class_id):
        self.current_class_id = class_id

    def update_select_button(self):
        can_select = True
        if not self.game_classes[self.current_class_id].is_selectable():
            can_select = False
        if self.select_button != None:
            self.select_button.set_enabled(can_select)
        return
