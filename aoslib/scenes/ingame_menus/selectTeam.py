from pyglet import gl
from aoslib.scenes import MenuScene
from aoslib.text import title_font
from aoslib.gui import create_large_navbar, TextButton, KeyDisplay
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR, TEAM_SPECTATOR, TEAM1, TEAM2, SECONDARY_MUSIC_BED_FADE_TIME, SECONDARY_MENU_MUSIC1
from . import draw_player_list
from shared import packet as packets
from aoslib import media, strings
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
from aoslib.scenes.main.gameClass import GameClass
import random
from shared.steam import SteamGetCurrentLobby

class SelectTeam(MenuScene):
    title = strings.CHOOSE_TEAM

    def on_start(self, menu=None, **kw):
        super(SelectTeam, self).on_start(menu, **kw)
        self.calculate_options()
        if not self.manager.classic:
            self.media.play('mu_start_game', zone=media.MUSIC_AUDIO_ZONE)
            if not self.media.is_playing_music(SECONDARY_MENU_MUSIC1):
                self.media.stop_music()
                self.media.play_music(SECONDARY_MENU_MUSIC1, self.config.music_volume, fade_speed_when_finished=1 / SECONDARY_MUSIC_BED_FADE_TIME)
        else:
            self.media.play('classic_mu_start_game', zone=media.MUSIC_AUDIO_ZONE)

    def on_stop(self):
        super(MenuScene, self).on_stop()

    def calculate_options(self):
        scene = self.manager.game_scene
        team1 = scene.team1
        team2 = scene.team2
        spectator = scene.spectator_team
        width = 225
        height = 49
        y = 149
        key_y = 480
        font_size = 25
        self.elements = []
        if not team1.locked:
            self.join_team1 = TextButton(strings.JOIN_TEAM.format(team1.name), 78, y, width, height, size=font_size)
            self.team1_key = KeyDisplay(93, key_y, '1')
            for element in (self.team1_key, self.join_team1):
                element.add_handler(self.on_select, TEAM1)

            self.elements += [self.join_team1, self.team1_key]
        if not team2.locked:
            self.join_team2 = TextButton(strings.JOIN_TEAM.format(team2.name), 497, y, width, height, size=font_size)
            self.team2_key = KeyDisplay(707, key_y, '2')
            for element in (self.join_team2, self.team2_key):
                element.add_handler(self.on_select, TEAM2)

            self.elements += [self.join_team2, self.team2_key]
        if self.manager.enable_spectator and not spectator.locked:
            dec = 13
            height -= dec
            y -= dec
            self.join_spectator = TextButton(strings.SPECTATE, 327, y, 110, height, size=15)
            self.spectator_key = KeyDisplay(458, y - 17, '3')
            for element in (self.join_spectator, self.spectator_key):
                element.add_handler(self.on_select, TEAM_SPECTATOR)

            self.elements += [self.join_spectator, self.spectator_key]
        self.navigation_bar = create_large_navbar()
        self.navigation_bar.add_handler(self.on_navigation)
        self.elements += [self.navigation_bar]

    def on_navigation(self, is_back):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        if is_back:
            self.media.stop_music(True)
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            self.parent.set_menu(LoadingMenu, back=True, from_server_menu=False)

    def on_select(self, value):
        scene = self.manager.game_scene
        team_selected = scene.teams[value]
        if not team_selected.locked:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            scene.team_selected(team_selected)
            if value == TEAM_SPECTATOR:
                from aoslib.scenes.main.gameScene import GameScene
                scene.create_player()
                self.set_scene(GameScene)
                scene.media.stop_music()
            elif team_selected.locked_class or not scene.class_selection_has_choices(team_selected):
                available_class_ids = []
                for id in scene.selected_team.class_list:
                    if id in self.manager.disabled_classes:
                        continue
                    available_class_ids.append(id)

                if len(available_class_ids) == 0:
                    available_class_ids.append(A553)
                if len(available_class_ids) == 1 and not self.manager.skin == 'mafia':
                    game_class = GameClass(self.manager, available_class_ids[0], self.manager.disabled_tools, self.manager.movement_speed_multipliers[available_class_ids[0]], self.config, self.manager.enable_fall_on_water_damage)
                else:
                    id = team_selected.class_list[random.randint(0, len(team_selected.class_list) - 1)]
                    game_class = GameClass(self.manager, id, disabled_tools=scene.manager.disabled_tools, speed_multiplier=self.manager.movement_speed_multipliers[id])
                scene.create_player(game_class)
                self.media.stop_music()
                from aoslib.scenes.main.gameScene import GameScene
                self.set_scene(GameScene)
            else:
                from aoslib.scenes.ingame_menus.selectClass import SelectClass
                self.parent.set_menu(SelectClass)

    def draw(self):
        scene = self.manager.game_scene
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = 800 / 2, 600 / 2
        for image in (global_images.large_frame, global_images.choose_team_frame):
            image.blit(mid_x, mid_y)

        title_font.draw(self.title.upper(), mid_x, 540, MENU_FONT_COLOR, center=True)
        y = 469
        width = 313
        height = 277
        draw_player_list(scene.team1, 77, y, width, height, 385)
        draw_player_list(scene.team2, 412, y, width, height, 415)
        for element in self.elements:
            element.draw()

    def update(self, dt):
        scene = self.manager.game_scene
        if scene.game_statistics_active:
            self.manager.set_menu(ViewGameStats)

    def packet_received(self, packet, sent_time):
        if packet.id == packets.LockTeam.id:
            self.calculate_options()
