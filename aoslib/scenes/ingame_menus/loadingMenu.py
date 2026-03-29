from pyglet import gl
from aoslib.scenes import MenuScene, ElementScene
from aoslib.text import Label, small_standard_ui_font, START_FONT, START_FONT_SIZE, medium_edo_ui_font, title_font, mode_name_font, START_FONT, ALDO_FONT, EDO_FONT
from aoslib.text import map_name_font, map_tagline_font, draw_text_lines, draw_text_within_boundaries, get_resized_font_and_formatted_text_to_fit_boundaries, chat_font
from aoslib.text import hc_font, draw_text_with_size_validation, navigation_font, small_title_aldo_font, big_title_aldo_font, draw_text_with_alignment_and_size_validation, medium_title_aldo_font
from aoslib.gui import TextButton
from aoslib.gui import create_large_navbar, TextButton
from aoslib.tools import get_server_details
from aoslib.images import global_images, load_ui, set_main_skin
from aoslib import image
from shared.common import clamp
from aoslib.common import collides
from aoslib.draw import draw_progress_bar
from aoslib.scenes.gui.editBoxControl import EditBoxControl
from shared.packet import InitialInfo, MapDataValidation, MapDataStart, MapDataEnd, MapSyncStart, MapSyncEnd, StateData, UGCMapInfo
from selectTeam import SelectTeam
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants import *
from aoslib.scenes.ingame_menus.scoreTypesDisplay import ScoreTypesDisplay
from aoslib.hud.hud import ViewGameStats
from shared.steam import SteamIsLoggedOn
from shared.constants_gamemode import A2445
from shared.constants_matchmaking import A2688, A2667
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.multiColumnPanelItem import MultiColumnPanelItem
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.frontend.panelBase import BACKGROUND_WITH_BOX
from pyglet.sprite import Sprite
from aoslib.draw import draw_quad
from shared.hud_constants import DARK_GREEN_COLOUR, UI_CONTROL_SPACING
from shared.steam import SteamGetCurrentLobby, SteamGetLobbyData, SteamGetFriendPersonaName, SteamGetLobbyOwner
from shared.constants_matchmaking import *

class LoadingMenu(MenuScene):
    title = strings.LOADING
    mode_name = ''
    map_name = ''
    percent = 0.0
    current_part = 0
    noof_parts = 3
    part_percent = 1.0 / float(noof_parts)
    current_load_infographic_image = None
    current_load_map_image = None
    current_load_mode = None
    current_load_classic = None
    from_server_menu = False
    initial_info_packet_count = 0
    done_set_skin = False
    done_quick_load = False
    current_tab_index = 0
    tab_timer = 0
    tab_timer_interupted = False
    infographic1_font = None
    infographic2_font = None
    infographic3_font = None
    map_preview = None
    custom_rules_expandable_list = None
    custom_game_rules = []
    category_list = []
    previous_menu = None
    last_percentage = 0
    connected = False

    def set_skin(self, skin):
        if not self.done_set_skin:
            self.done_set_skin = True
            self.done_quick_load = False
            image.set_texture_skin(skin)

    def quick_load_skin(self):
        if not self.done_quick_load and image.IMAGE_SKIN != image.OLD_IMAGE_SKIN:
            self.done_quick_load = True
            set_main_skin(image.IMAGE_SKIN)

    def full_load_skin(self):
        pass

    def set_loading_image(self, map_name, mode, classic, texture_skin):
        self.set_skin(texture_skin)
        self.quick_load_skin()
        self.classic = classic
        self.map_name = map_name
        if texture_skin == 'mafia':
            image_name = global_images.mafia_loading_infographic_imagenames[mode]
        elif classic == CLASSIC:
            image_name = global_images.classic_loading_infographic_imagenames[mode]
        else:
            image_name = global_images.not_classic_loading_infographic_imagenames[mode]
        mapimage_name = ''
        if self.map_name is not '':
            if self.map_name in global_images.loading_map_imagenames:
                mapimage_name = global_images.loading_map_imagenames[self.map_name]
            else:
                mapimage_name = global_images.loading_map_imagenames['Default_map_image']
        loading = [
         'game_loading']
        infographics = ['mode_infographics']
        mapimages = ['map_images']
        self.current_load_infographic_image = load_ui(self.current_load_infographic_image, loading + infographics + [image_name], scale=global_images.global_scale, center=True, filtered=False)
        if mapimage_name is not '':
            self.current_load_map_image = load_ui(self.current_load_map_image, loading + mapimages + [mapimage_name], scale=global_images.global_scale, center=True, filtered=False)
            if not self.current_load_map_image:
                print "Couldn't load map image"
            else:
                self.current_load_infographic_image.width = 650
                self.current_load_infographic_image.height = 305

    def initialize(self):
        self.status_text = ''
        self.navigation_bar = create_large_navbar()
        self.navigation_bar.add_handler(self.on_navigation)
        self.start_button = TextButton(strings.START, 492, 151, 246, 58, size=40)
        self.start_button.add_handler(self.start_pressed)
        pad = 0
        self.map_name_text = Label('', x=83, y=377, width=360, height=60, align='left', anchor_x='left', anchor_y='top', font_name=ALDO_FONT, font_size=61, color=MAP_NAME_FONT_COLOR)
        self.map_tagline_text = Label('', x=83, y=372, width=320, height=30, align='left', anchor_x='left', anchor_y='bottom', font_name=ALDO_FONT, font_size=20, color=MAP_NAME_FONT_COLOR)
        self.mode_text = Label('', x=240, y=436, width=320, height=50, align='center', anchor_x='left', anchor_y='center', font_name=ALDO_FONT, font_size=38, color=MODE_NAME_FONT_COLOR)
        self.map_title_font = big_title_aldo_font
        self.elements = [self.navigation_bar, self.start_button]
        self.ready_message = None
        self.map_tagline = ''
        self.scoreTypesDisplay = ScoreTypesDisplay(self.manager)
        self.elements.append(self.scoreTypesDisplay)
        self.max_custom_rules_height = 200
        self.custom_rules_expandable_list = ExpandableListPanel(self.manager)
        self.elements.append(self.custom_rules_expandable_list)
        self.map_preview = None
        self.map_preview_x = 469
        self.map_preview_y = 194
        self.map_preview_scale = 1.0
        self.password_box = EditBoxControl('', 70, 180, 350, 20, center=False, empty_text='Type the server password and press enter to continue.', draw_background=False, return_on_focus_loss=False)
        self.password_box.visible = False
        self.password_box.is_password = True
        self.password_box.font = navigation_font
        self.password_box.allow_over_typing = True
        self.elements.append(self.password_box)
        return

    def send_password_callback(self):
        password_provided = False
        password_provided.password = self.password_box.visible_text
        self.password_box.visible = False
        self.manager.client.send_packet(password_provided)

    def on_text(self, value):
        if self.password_box.visible:
            if value == u'\r':
                self.send_password_callback()
            self.password_box.on_text(value)

    def initialize_from_frontend(self):
        self.custom_game_rules = []
        self.category_list = []
        self.custom_rules_expandable_list.reset_list()
        self.current_load_infographic_image = None
        self.current_load_map_image = None
        self.map_preview = None
        self.map_title_font = big_title_aldo_font
        self.map_tagline_text.text = ''
        self.infographic1_lines = []
        self.infographic2_lines = []
        self.infographic3_lines = []
        self.mode_text.text = ''
        self.map_name_text.text = ''
        self.tab_timer_interupted = False
        self.tab_timer = 0
        self.current_tab_index = 0
        self.init_tabs('', '')
        return

    def on_navigation(self, is_back):
        if is_back:
            if self.previous_menu is None:
                self.manager.set_main_menu()
            else:
                self.manager.disconnect()
                self.manager.set_menu(self.previous_menu, back=True)
            self.media.stop_sounds()
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        return

    def on_start(self, identifier=None, server_mode=SERVERMODE_PUBLIC, name=None, from_server_menu=True, expected_map=None, expected_mode=None, expected_classic=NOT_CLASSIC, expected_skin=None, previous_menu=None):
        if from_server_menu:
            self.previous_menu = previous_menu
        self.done_set_skin = False
        self.from_server_menu = from_server_menu
        if from_server_menu:
            self.initialize_from_frontend()
        if expected_mode is not None:
            self.set_loading_image(expected_map, expected_mode, expected_classic, expected_skin)
        self.ready_message = None
        self.load_completed = False
        self.manager.showing_loading_screen = True
        self.current_part = 0
        self.initial_info_packet_count = 0
        self.receiving_packs = self.receiving_map = False
        self.no_progress_timeout = LOADING_MENU_NO_PROGRESS_TIMEOUT
        self.last_percentage = 0.0
        self.connected = False
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if identifier is not None:
            host, port = get_server_details(identifier)
            self.manager.connect(host, port, server_mode, name, from_server_menu)
            self.status_text = strings.CONNECTING_TO_SERVER
            self.start_button.set_enabled(False)
            self.start_button.set_glow(False)
        elif not self.manager.show_game_scene:
            self.on_map_transfer()
        if not self.manager.show_game_scene:
            self.start_button.set_enabled(False)
            self.start_button.set_glow(False)
        return

    def init_tabs(self, map_name, mode_name):
        self.tabs = []
        tab_map = Label(strings.MAP, font_name=EDO_FONT, font_size=16, anchor_x='center')
        self.tabs.append(tab_map)
        if map_name != 'Training' and map_name != '':
            tab_mode = Label(strings.MODE, font_name=EDO_FONT, font_size=16, anchor_x='center')
            self.tabs.append(tab_mode)
            if mode_name != 'MAP_CREATOR':
                tab_scores = Label(strings.SCORES, font_name=EDO_FONT, font_size=16, anchor_x='center')
                self.tabs.append(tab_scores)

    def on_stop(self):
        super(LoadingMenu, self).on_stop()
        self.manager.showing_loading_screen = False

    def on_pack_transfer(self):
        self.status_text = strings.RECEIVING_SERVER_PACKS
        self.receiving_packs = True
        self.receiving_map = False

    def on_map_transfer(self):
        self.receiving_packs = False
        self.receiving_map = True

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = 800 / 2, 600 / 2
        if global_images.large_frame is not None:
            global_images.large_frame.blit(mid_x, mid_y)
        if global_images.loading_bar_bg is not None:
            global_images.loading_bar_bg.blit(mid_x - 340, mid_y - 205)
        self.draw_tabs()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.current_tab_index == 0:
            self.draw_map_tab()
        elif self.current_tab_index == 1:
            self.draw_infographic_tab()
        elif self.current_tab_index == 2:
            self.draw_scores_tab()
        if self.current_tab_index == 0:
            if len(self.custom_game_rules) > 0:
                self.custom_rules_expandable_list.visible = True
            else:
                self.custom_rules_expandable_list.visible = False
        else:
            self.custom_rules_expandable_list.visible = False
        pad = 20
        width = 800 - pad * 2
        if self.manager.show_game_scene or not self.manager.client:
            percentage = 1.0
        else:
            percentage = self.part_percent * self.current_part + clamp(self.manager.client.map_percentage) * self.part_percent
        for element in self.elements:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            if not element.visible:
                continue
            element.draw()

        pad = 4
        draw_progress_bar(percentage, 62 + pad, 95 + pad, 422 - pad * 2, 58 - pad * 2)
        x = 450
        width = 320
        height = 45
        return

    def draw_tabs(self):
        tab_frame_x = 119
        tab_x = tab_frame_x
        tab_y = 481
        mid_x, mid_y = 800 / 2, 600 / 2
        title_font.draw(self.title.upper(), mid_x, 540, MENU_FONT_COLOR, center=True)
        old_width = global_images.generic_tab_active.width
        old_height = global_images.generic_tab_active.height
        new_width = 224
        new_height = 42
        global_images.generic_tab_active.width = new_width
        global_images.generic_tab_active.height = new_height
        global_images.generic_tab_inactive.width = new_width
        global_images.generic_tab_inactive.height = new_height
        if global_images.loading_tab_bg is not None:
            global_images.loading_tab_bg.blit(mid_x, mid_y + 13)
        for index, tab in enumerate(self.tabs):
            if index == self.current_tab_index:
                global_images.generic_tab_active.blit(tab_frame_x, tab_y - 1)
                tab.color = MENU_FONT_COLOR2
            else:
                global_images.generic_tab_inactive.blit(tab_frame_x, tab_y - 1)
                tab.color = MENU_FONT_COLOR
            tab.x = tab_frame_x + 48
            tab.y = tab_y
            tab.draw()
            tab_frame_x += new_width + UI_CONTROL_SPACING

        global_images.generic_tab_inactive.width = old_width
        global_images.generic_tab_inactive.height = old_height
        global_images.generic_tab_active.width = old_width
        global_images.generic_tab_active.height = old_height
        return

    def draw_scores_tab(self):
        mid_x = 400
        mid_y = 313
        if self.current_load_map_image is not None:
            self.current_load_map_image.blit(mid_x, mid_y)
        self.scoreTypesDisplay.draw()
        return

    def draw_infographic_tab(self):
        mid_x = 400
        mid_y = 313
        if self.current_load_map_image is not None:
            self.current_load_map_image.blit(mid_x, mid_y)
        if self.current_load_infographic_image is not None:
            self.current_load_infographic_image.blit(mid_x, mid_y)
        if self.infographic1_font is not None:
            draw_text_lines(self.infographic1_lines, 105, 193, 177, 40, self.infographic1_font, 2, INFOGRAPHIC_TEXT_COLOR, horizontal_alignment='center', vertical_alignment='center')
        if self.infographic2_font is not None:
            draw_text_lines(self.infographic2_lines, 315, 186, 177, 39, self.infographic2_font, 2, INFOGRAPHIC_TEXT_COLOR, horizontal_alignment='center', vertical_alignment='center')
        if self.infographic3_font is not None:
            draw_text_lines(self.infographic3_lines, 536, 187, 177, 47, self.infographic3_font, 2, INFOGRAPHIC_TEXT_COLOR, horizontal_alignment='center', vertical_alignment='center')
        x = 230
        width = 320
        height = 45
        self.mode_text.draw_shadowed(False, MAP_NAME_DROPSHADOW_COLOR, 2)
        self.mode_text.draw_shadowed(False, MAP_NAME_DROPSHADOW_COLOR, 3)
        self.mode_text.draw_stroked(True, 2, MAP_NAME_DROPSHADOW_COLOR)
        return

    def draw_map_tab(self):
        mid_x = 400
        mid_y = 313
        if self.current_load_map_image is not None:
            self.current_load_map_image.blit(mid_x, mid_y)
        draw_text_with_size_validation(self.status_text, 405, 25, 315, 30, MENU_FONT_COLOR, font=navigation_font)
        draw_text_with_alignment_and_size_validation(self.map_name_text.text, self.map_name_text.x, self.map_name_text.y, self.map_name_text.width, self.map_name_text.height, MAP_NAME_FONT_COLOR, self.map_title_font, 'left', 'top', True, True, 3, 2)
        draw_text_with_alignment_and_size_validation(self.map_tagline_text.text, self.map_tagline_text.x, self.map_tagline_text.y, self.map_tagline_text.width, self.map_tagline_text.height, MAP_NAME_FONT_COLOR, small_title_aldo_font, 'left', 'top', True, True)
        if self.map_preview:
            global_images.loading_map_frame.width = 258
            global_images.loading_map_frame.height = 258
            global_images.loading_map_frame.blit(self.map_preview_x - 10, self.map_preview_y - 10)
            self.map_preview._get_image().width = 238
            self.map_preview._get_image().height = 238
            self.map_preview.scale = self.map_preview_scale
            self.map_preview.draw()
        return

    def set_tab(self, index):
        self.current_tab_index = index
        self.custom_rules_expandable_list.scrollbar.set_scroll(0, True)
        self.scoreTypesDisplay.score_types_expandable_list.scrollbar.set_scroll(0, True)

    def on_mouse_press(self, x, y, button, modifiers):
        self.tab_timer_interupted = True
        new_width = 220
        new_height = 42
        x1 = 62
        x2 = x1 + new_width + 5
        y1 = 430 + global_images.generic_tab_active.height
        y2 = y1 + new_height
        for index, tab in enumerate(self.tabs):
            if collides(x1, y1, x2, y2, x, y, x, y):
                self.set_tab(index)
                return
            x2 += new_width + 10

        MenuScene.on_mouse_press(self, x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        self.tab_timer_interupted = True
        if self.password_box.visible:
            self.password_box.set_focus(True)
            self.password_box.on_key_press(symbol, modifiers)
        MenuScene.on_key_press(self, symbol, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.tab_timer_interupted = True
        MenuScene.on_mouse_scroll(self, x, y, scroll_x, scroll_y)

    def on_connect(self):
        self.connected = True

    def load_complete(self):
        self.ready_message = strings.MAP_READY.format(self.map_name)
        self.status_text = ''
        self.start_button.set_enabled(True)
        self.start_button.set_glow(True)
        scene = self.manager.game_scene
        skybox_name = scene.get_skybox_name()
        if skybox_name:
            scene.set_skybox_name(skybox_name)
        scene.set_ground_colors()

    def update(self, dt):
        if self.manager.show_game_scene or not self.manager.client:
            percentage = 1.0
        else:
            percentage = self.part_percent * self.current_part + clamp(self.manager.client.map_percentage) * self.part_percent
        if percentage < 1.0 and percentage == self.last_percentage:
            self.no_progress_timeout -= dt
            if self.no_progress_timeout <= 0:
                self.on_navigation(is_back=True)
                self.manager.set_big_text_message(ERROR_TIMEOUT)
                print 'Failed to complete map load'
        else:
            self.last_percentage = percentage
            self.no_progress_timeout = LOADING_MENU_NO_PROGRESS_TIMEOUT
        from aoslib.gamemanager import GameManager
        if not SteamIsLoggedOn() or GameManager.invalid_data_error:
            self.manager.disconnect()
            from aoslib.scenes.frontend.selectMenu import SelectMenu
            self.manager.set_menu(SelectMenu, back=True)
            return
        super(LoadingMenu, self).update(dt)
        self.start_button.update()
        self.tab_timer += dt
        if self.tab_timer >= A2494 and not self.tab_timer_interupted:
            self.tab_timer = 0
            if self.current_tab_index < len(self.tabs) - 1:
                self.current_tab_index += 1
            elif A2495:
                self.current_tab_index = 0
        if self.manager.game_scene.load_next_ugc_prefab():
            if self.connected and not self.load_completed:
                self.load_complete()
                self.load_completed = True

    def close_menu(self):
        from aoslib.scenes.main.gameScene import GameScene
        self.set_scene(GameScene)

    def start_pressed(self):
        self.media.stop_music(True)
        self.ready_message = None
        scene = self.manager.game_scene
        if scene.state_data.has_map_ended or scene.game_statistics_active:
            scene.show_game_statistics(True)
            scene.manager.set_menu(ViewGameStats)
            scene.on_map_ended()
        else:
            scene.vip_health_multiplier = 1.0
            for rule in self.custom_game_rules:
                if rule[1] == strings.RULE_VIP_HEALTH:
                    if rule[2] in A2682:
                        scene.vip_health_multiplier = A2682[rule[2]]

            scene.set_ground_colors()
            if scene.force_team_join is None:
                self.parent.set_menu(SelectTeam)
            else:
                team = scene.teams[scene.force_team_join]
                scene.team_selected(team)
                if team.locked_class:
                    scene.create_player()
                    self.close_menu()
                elif scene.is_in_ugc_mode():
                    from aoslib.scenes.ingame_menus.selectPrefabs import SelectPrefabs
                    self.parent.set_menu(SelectPrefabs)
                else:
                    from aoslib.scenes.ingame_menus.selectClass import SelectClass
                    self.parent.set_menu(SelectClass)
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        return

    def add_category(self, name, column_widths, category_texts):
        category_row = CategoryListItem(name, is_expandable=True, sub_row_colours=[(87, 83, 74, 150), (54, 51, 44, 150)])
        rows = []
        for column_texts in category_texts:
            row = MultiColumnPanelItem(column_widths, column_texts)
            row.selectable_row = False
            row.center_text = False
            rows.append(row)

        self.custom_rules_expandable_list.add_list_item(category_row, rows)

    def get_game_rule_catagory(self, rule_name):
        for catagory in A2667:
            for rule in A2667[catagory]:
                if rule_name == rule:
                    return catagory

    def setup_custom_game_rules(self):
        self.custom_rules_expandable_list.reset_list()
        if len(self.custom_game_rules) > 0:
            self.custom_rules_expandable_list.initialise_ui(strings.CUSTOM_GAME_RULES, 83, 384, 366, self.max_custom_rules_height, has_header=True, enable_background_resizing=True, category_spacing_colour=DARK_GREEN_COLOUR)
            self.custom_rules_expandable_list.set_background(background=BACKGROUND_WITH_BOX, background_colour=(0,
                                                                                                                0,
                                                                                                                0,
                                                                                                                150))
            self.custom_rules_expandable_list.visible = False
            self.custom_rules_expandable_list.center_header_text = True
            for category in sorted(self.category_list, key=(lambda category: category)):
                category_rules = []
                column_widths = [
                 240, 60]
                for rule in self.custom_game_rules:
                    if rule[0] == category:
                        column_rule = (
                         rule[1], rule[2])
                        category_rules.append(column_rule)

                self.add_category(category, column_widths, category_rules)

            height = self.custom_rules_expandable_list.get_total_height_of_rows()
            max_height = self.max_custom_rules_height
            if height > max_height:
                height = max_height
            self.custom_rules_expandable_list.visible = True
        self.custom_rules_expandable_list.on_scroll(0, True)

    def create_ugc_preview_image(self, png_memory):
        map_preview_image = image.load_texture_from_memory(png_memory, scale=global_images.global_scale)
        if map_preview_image is not None:
            self.map_preview = Sprite(map_preview_image, self.map_preview_x, self.map_preview_y)
        return

    def packet_received(self, packet, sent_time):
        # if packet.id == PasswordNeeded.id:
        #     self.status_text = ''
        #     self.password_box.set('')
        #     self.password_box.visible = True
        if packet.id == InitialInfo.id:
            if self.initial_info_packet_count > 0:
                self.current_part = 0
            self.initial_info_packet_count += 1
            prev_map_name = self.map_name
            self.map_name = packet.map_name
            self.init_tabs(self.map_name, packet.mode_name)
            try:
                self.map_tagline = strings.get_by_id(MAP_NAME_TAGLINES[packet.map_name])
                self.map_title_font = medium_title_aldo_font
            except KeyError:
                self.map_tagline = ''

            self.map_tagline_text.text = self.map_tagline
            if self.map_name == u'Training':
                self.map_name_text.text = strings.TUTORIAL_MODE_TITLE
            else:
                self.map_name_text.text = self.map_name
            lobby_id = SteamGetCurrentLobby()
            custom_ugc_map = SteamGetLobbyData(lobby_id, 'Custom_UGC_Map')
            if packet.mode_name == 'MAP_CREATOR' or custom_ugc_map == 'True':
                custom_ugc_map_author = SteamGetLobbyData(lobby_id, 'Custom_UGC_Map_Author')
                ugc_title = SteamGetLobbyData(lobby_id, 'MAP_ROTATION_NEW_TITLE')
                if ugc_title:
                    self.map_name_text.text = ugc_title
                if custom_ugc_map_author != '':
                    self.map_title_font = medium_title_aldo_font
                    self.map_tagline_text.text += '- ' + custom_ugc_map_author
            self.manager.game_scene.map_name = self.map_name
            mode_name = packet.mode_name
            if packet.classic == CLASSIC:
                mode_name = 'CLASSIC_' + mode_name
            self.set_loading_image(packet.map_name, packet.mode_key, packet.classic, packet.texture_skin)
            self.mode_name = strings.get_by_id(mode_name).upper()
            self.mode_text.text = self.mode_name
            self.map_preview = None
            if packet.map_is_ugc == MAP_IS_UGC_HOST:
                ugc_data = self.manager.client.ugc_data
                if ugc_data is None:
                    png_data = None
                else:
                    png_data = ugc_data.load_png(silent=True)
                if png_data is None:
                    self.map_preview = None
                else:
                    self.create_ugc_preview_image(png_data)
            if self.map_preview is None:
                if self.map_name in global_images.map_previews:
                    map_preview = global_images.map_previews[self.map_name][2]
                    self.map_preview = Sprite(map_preview, self.map_preview_x, self.map_preview_y)
            self.infographic1_font, self.infographic1_lines = get_resized_font_and_formatted_text_to_fit_boundaries(strings.get_by_id(packet.mode_infographic_text1), 180, 35, map_tagline_font, 2)
            self.infographic2_font, self.infographic2_lines = get_resized_font_and_formatted_text_to_fit_boundaries(strings.get_by_id(packet.mode_infographic_text2), 180, 35, map_tagline_font, 2)
            self.infographic3_font, self.infographic3_lines = get_resized_font_and_formatted_text_to_fit_boundaries(strings.get_by_id(packet.mode_infographic_text3), 180, 35, map_tagline_font, 2)
            self.status_text = strings.CHECKING_MAP.format(self.map_name)
            score_filter = [packet.mode_key, A2435]
            self.scoreTypesDisplay.setup_scores(mode_filter=score_filter, friendly_fire=packet.friendly_fire)
            self.custom_game_rules = []
            self.category_list = []
            if packet.mode_key != A2445:
                for custom_rule in packet.custom_game_rules:
                    category = self.get_game_rule_catagory(custom_rule[0])
                    if category in A2448:
                        category_name = strings.get_by_id(A2448[category])
                        category_name = ('').join(e for e in category_name if e.isalnum())
                    else:
                        category_name = strings.get_by_id(category).upper()
                    if category_name not in self.category_list:
                        self.category_list.append(category_name)
                    custom_game_rule = (
                     category_name, strings.get_by_id(custom_rule[0]), custom_rule[1])
                    self.custom_game_rules.append(custom_game_rule)

            self.setup_custom_game_rules()
        elif packet.id == UGCMapInfo.id:
            if packet.png_data is not None:
                self.create_ugc_preview_image(packet.png_data)
                print 'UGC map preview receieved'
        elif packet.id == MapDataValidation.id:
            self.status_text = strings.LOADING_MAP.format(self.map_name)
        elif packet.id == MapDataStart.id:
            self.status_text = strings.RECEIVING_MAP.format(self.map_name)
        elif packet.id == MapSyncStart.id:
            self.current_part += 1
            self.status_text = strings.SYNCING_MAP.format(self.map_name)
        elif packet.id == MapSyncEnd.id:
            self.current_part += 1
            self.status_text = strings.INITIALISING_MAP.format(self.map_name)
            self.full_load_skin()
        return
