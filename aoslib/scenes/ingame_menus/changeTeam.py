from pyglet import gl
from pyglet.window import key
from aoslib.scenes import MenuScene
from aoslib.text import title_font, team_list_font
from aoslib.gui import KeyDisplay, TextButton
from aoslib.images import global_images
from shared.constants import *
from . import draw_player_list
from shared import packet as packets
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.scenes.main.gameClass import GameClass
import random

class ChangeTeam(MenuScene):
    title = strings.CHANGE_TEAM

    def on_start(self, menu=None, **kw):
        super(ChangeTeam, self).on_start(menu, **kw)
        self.calculate_options()

    def calculate_options(self):
        key_y = 455
        game_scene = self.manager.game_scene
        team1 = game_scene.team1
        team2 = game_scene.team2
        spectator = game_scene.spectator_team
        forced_team = game_scene.force_team_join
        self.elements = []
        y = 104
        button_y = y + 25
        width = 200
        height = 49
        font_size = 20
        if not team1.locked and (forced_team is None or forced_team == team1.id) and (game_scene.first_chosen_team is not team2 or not game_scene.state_data.lock_team_swap or team1.count() == 0 or team2.count() - team1.count() >= TEAM_LOCK_DIFFERENCE_COUNT_TOLERANCE or team2.locked):
            x = 93
            self.team1_key = KeyDisplay(x, key_y, '1')
            self.team1_key.add_handler(self.on_select, TEAM1)
            self.team1_join_button = TextButton(strings.JOIN_TEAM.format(team1.name), x - 25, button_y, width, height, font_size)
            self.team1_join_button.add_handler(self.on_select, TEAM1)
            self.elements += [self.team1_key, self.team1_join_button]
        if not team2.locked and (forced_team is None or forced_team == team2.id) and (game_scene.first_chosen_team is not team1 or not game_scene.state_data.lock_team_swap or team2.count() == 0 or team1.count() - team2.count() >= TEAM_LOCK_DIFFERENCE_COUNT_TOLERANCE or team1.locked):
            x = 707
            self.team2_key = KeyDisplay(x, key_y, '2')
            self.team2_key.add_handler(self.on_select, TEAM2)
            self.team2_join_button = TextButton(strings.JOIN_TEAM.format(team2.name), x - 176, button_y, width, height, font_size)
            self.team2_join_button.add_handler(self.on_select, TEAM2)
            self.elements += [self.team2_key, self.team2_join_button]
        if self.manager.enable_spectator and not spectator.locked:
            x = 464
            self.spectator_key = KeyDisplay(x, y, '3')
            self.spectator_key.add_handler(self.on_select, TEAM_SPECTATOR)
            self.join_spectator = TextButton(strings.SPECTATE, x - 150, button_y - 6, 130, height - 10, font_size - 5)
            self.join_spectator.add_handler(self.on_select, TEAM_SPECTATOR)
            self.elements += [self.spectator_key, self.join_spectator]
            if game_scene.state_data.lock_spectator_swap:
                self.join_spectator.enabled = False
            else:
                self.join_spectator.enabled = True
        return

    def on_select(self, value):
        game_scene = self.manager.game_scene
        team = game_scene.teams[value]
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if not team.locked:
            game_scene.team_changed(team)
            if value == TEAM_SPECTATOR:
                from aoslib.scenes.main.gameScene import GameScene
                self.set_scene(GameScene)
            elif team.locked_class or not game_scene.class_selection_has_choices(team):
                was_spectator = game_scene.player and game_scene.player.team and game_scene.player.team.id == TEAM_SPECTATOR
                available_class_ids = []
                for id in game_scene.selected_team.class_list:
                    if id in self.manager.disabled_classes:
                        continue
                    available_class_ids.append(id)

                if len(available_class_ids) == 0:
                    available_class_ids.append(DEFAULT_CLASS)
                if len(available_class_ids) == 1 and not self.manager.is_in_mafia_mode():
                    game_class = GameClass(game_scene.manager, available_class_ids[0], disabled_tools=game_scene.manager.disabled_tools, speed_multiplier=game_scene.manager.movement_speed_multipliers[available_class_ids[0]])
                else:
                    class_id = team.class_list[random.randint(0, len(team.class_list) - 1)]
                    game_class = GameClass(game_scene.manager, class_id, disabled_tools=game_scene.manager.disabled_tools, speed_multiplier=game_scene.manager.movement_speed_multipliers[class_id])
                if was_spectator:
                    game_scene.create_player(game_class)
                else:
                    game_scene.class_changed(game_class)
                self.media.stop_music()
                from aoslib.scenes.main.gameScene import GameScene
                self.set_scene(GameScene)
            else:
                from aoslib.scenes.ingame_menus.selectClass import SelectClass
                self.parent.set_menu(SelectClass, in_game_menu=True, previous_menu=type(self))

    def draw(self):
        scene = self.manager.game_scene
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = 800 / 2, 600 / 2
        global_images.change_team_frame.blit(mid_x, mid_y)
        title_font.draw(self.title.upper(), mid_x, 489, MENU_FONT_COLOR, center=True)
        y = 443
        width = 313
        height = 263
        draw_player_list(scene.team1, 77, y, width, height, 385)
        draw_player_list(scene.team2, 412, y, width, height, 415)
        for element in self.elements:
            element.draw()

    def on_key_press(self, symbol, modifiers):
        MenuScene.on_key_press(self, symbol, modifiers)
        config = self.config
        if symbol != config.change_team and symbol != config.menu:
            return
        from aoslib.scenes.main.gameScene import GameScene
        self.set_scene(GameScene)
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)

    def packet_received(self, packet, sent_time):
        if packet.id == packets.LockTeam.id or packet.id == packets.ForceTeamJoin.id or packet.id == packets.CreatePlayer.id or packet.id == packets.ExistingPlayer.id:
            self.calculate_options()
