from aoslib.scenes import MenuScene
from aoslib.common import collides
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_size_validation, get_resized_font_and_formatted_text_to_fit_boundaries, title_font, draw_text_lines, big_edo_ui_font
from aoslib.gui import TextButton
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
from shared.steam import SteamGetInternetServerList
from shared.constants import SERVERMODE_RANKED, SERVERMODE_PUBLIC, SERVERMODE_TUTORIAL
from shared.common import clamp
from serverInfo import ServerInfo
import playlists
GET_SERVER_TIME = 3.0
MAXIMUM_PING = 0.04

class JoiningGameMenu(MenuScene):
    config = None
    playlist_id = 0
    text_font = None
    text_lines = []

    def initialize(self):
        self.reset()

    def reset(self):
        self.query_client = None
        self.servers_count = 0
        self.server_responses = []
        self.lowest_ping = 0
        self.getting_servers = 0.0
        self.server_mode = SERVERMODE_PUBLIC
        return

    def on_menu_opened(self):
        self.reset()
        self.elements = []
        self.text_width = 443
        self.text_height = 70
        pad = 5
        x = 156 + pad
        width = 493 / 2 - pad * 2
        font_size = 30
        height = 71 - pad * 2
        y = 113 - pad
        self.cancel_button_x = x
        self.cancel_button = TextButton(strings.CANCEL, self.cancel_button_x, y, width, height, font_size)
        self.cancel_button.add_handler(self.cancel_pressed)
        self.elements.append(self.cancel_button)
        x += width + pad
        self.start_button = TextButton(strings.START, x, y, width, height, font_size)
        self.start_button.add_handler(self.start_pressed)
        self.elements.append(self.start_button)
        self.start_button.enabled = False

    def on_start(self, menu=None, config=None, server_mode=SERVERMODE_PUBLIC, playlist_id=0, previous_menu=None):
        self.on_menu_opened()
        self.previous_menu = previous_menu
        self.config = config
        self.server_mode = server_mode
        self.playlist_id = playlist_id
        if server_mode == SERVERMODE_RANKED:
            self.title = strings.RANKED_MATCH
        elif server_mode == SERVERMODE_TUTORIAL:
            self.title = strings.TUTORIAL_MODE_TITLE
        else:
            self.title = strings.QUICK_MATCH
        self.set_text(strings.SEARCHING_FOR_SERVERS)
        steam_successful = SteamGetInternetServerList(server_mode, self.got_server_callback, self.finished_getting_servers_callback)
        if steam_successful:
            self.getting_servers = GET_SERVER_TIME
            self.lowest_ping = 1000.0
            self.server_responses = []

    def on_stop(self):
        self.reset()

    def close(self):
        self.reset()

    def on_key_press(self, symbol, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        width = 473
        x1 = 163
        x2 = x1 + width
        y1 = 467
        y2 = 500
        if collides(x1, y1, x2, y2, x, y, x, y):
            index = int((x - x1) / float(width / 3))
            self.set_tab(index)
            return
        super(JoiningGameMenu, self).on_mouse_press(x, y, button, modifiers)

    def start_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.reset()
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)

    def cancel_pressed(self):
        tutorial = self.server_mode == SERVERMODE_TUTORIAL
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        self.reset()
        if tutorial:
            from selectMenu import SelectMenu
            self.parent.set_menu(SelectMenu, back=True)
        else:
            from quickPlayMenu import QuickPlayMenu
            self.parent.set_menu(QuickPlayMenu, back=True)

    def update(self, dt):
        if self.getting_servers > 0.0:
            self.getting_servers -= dt
            if self.getting_servers <= 0.0:
                self.getting_servers = 0.0
                if self.servers_count > 0 and self.lowest_ping < MAXIMUM_PING:
                    self.select_quick_match_server()
                else:
                    self.getting_servers = GET_SERVER_TIME

    def draw(self):
        mid_x, mid_y = (400, 300)
        y = mid_y
        title_y = 534
        logo_y = mid_y + 45
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.small_frame.blit(mid_x, y)
        if self.server_mode == SERVERMODE_TUTORIAL:
            global_images.searching_tutorial.blit(mid_x, logo_y)
        else:
            global_images.searching_logo.blit(mid_x, logo_y)
        title_x = 206
        title_y = 520
        title_width = global_images.small_frame.width - 190
        title_height = 50
        draw_text_with_size_validation(self.title.upper(), title_x, title_y, title_width, title_height, MENU_FONT_COLOR, font=title_font)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.start_button.enabled == False and self.cancel_button.enabled:
            self.cancel_button.x = mid_x - self.cancel_button.width * 0.5
        else:
            self.cancel_button.x = self.cancel_button_x
        for element in self.elements:
            if not element.enabled:
                continue
            element.draw()

        text_x = 180
        text_y = 140
        if self.text_lines is not None and len(self.text_lines) > 0:
            draw_text_lines(self.text_lines, text_x, text_y, self.text_width, self.text_height, self.text_font, 4.0, MENU_FONT_COLOR, 'center', 'center')
        return

    def finished_getting_servers_callback(self):
        if self.getting_servers > 0.0:
            self.getting_servers = 0.0
            self.select_quick_match_server()

    def got_server_callback(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        print("I got calledback")
        server = ServerInfo(name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played)
        print "Server Info: ", server
        print "Server Match: ", server.is_matching_version
        if not server.is_matching_version:
            print "Not matching version"
            return
        if self.playlist_id != 0 and int(self.playlist_id) != int(server.playlist_id):
            print "Not matching playlist"
            return
        self.servers_count += 1
        self.server_responses.append(server)
        # self.on_server_response(server, server.ping)

    def on_server_response(self, server, ping):
        if ping < self.lowest_ping:
            self.lowest_ping = ping
        self.server_responses.append(server)

    def set_text(self, text):
        self.text_font, self.text_lines = get_resized_font_and_formatted_text_to_fit_boundaries(text, self.text_width, self.text_height, big_edo_ui_font, 2, True)

    def select_quick_match_server(self):
        self.getting_servers = 0.0
        low_ping_servers = []
        populated_servers = []
        empty_servers = []
        empty_low_ping_servers = []
        low_ping = self.lowest_ping * 3
        for server in self.server_responses:
            if server.count > 0 and server.count < server.max:
                if server.ping < low_ping:
                    low_ping_servers.append(server)
                else:
                    populated_servers.append(server)
            elif server.count == 0:
                if server.ping < low_ping:
                    empty_low_ping_servers.append(server)
                else:
                    empty_servers.append(server)

        import random
        noof_empty_low_ping_servers = len(empty_low_ping_servers)
        noof_low_ping_servers = len(low_ping_servers)
        noof_populated_servers = len(populated_servers)
        noof_empty_servers = len(empty_servers)
        if noof_low_ping_servers == 0 and noof_empty_low_ping_servers == 0 and noof_populated_servers == 0 and noof_empty_servers == 0:
            self.set_text(strings.NO_SERVERS_FOUND)
            return
        else:
            if noof_low_ping_servers > 0:
                index = random.randint(0, noof_low_ping_servers - 1)
                server = low_ping_servers[index]
            elif noof_empty_low_ping_servers > 0:
                index = random.randint(0, noof_empty_low_ping_servers - 1)
                server = empty_low_ping_servers[index]
            elif noof_populated_servers > 0:
                index = random.randint(0, noof_populated_servers - 1)
                server = populated_servers[index]
            else:
                index = random.randint(0, noof_empty_servers - 1)
                server = empty_servers[index]
            if self.query_client is not None:
                self.query_client.stop()
                self.query_client = None
            self.server_responses = []
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            expected_mode = server.mode_id
            expected_classic = server.classic
            expected_skin = server.texture_skin
            self.parent.set_menu(LoadingMenu, identifier=server.identifier, server_mode=self.server_mode, name=server.name, from_server_menu=True, expected_map=server.map, expected_mode=expected_mode, expected_classic=expected_classic, expected_skin=expected_skin, previous_menu=self.previous_menu)
            return
