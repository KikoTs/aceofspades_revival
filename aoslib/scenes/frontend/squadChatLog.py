from shared.steam import SteamRegisterLobbyChatCallback, SteamRegisterLobbyUpdateCallback, SteamGetLobbyMemberName, SteamSendChatMessage, GetUserSteamID, SteamGetLobbyOwner
from aoslib.text import split_text_to_fit_screen, chat_font, chat_font_tuffy, draw_text_with_size_validation
from shared.constants import MENU_FONT_COLOR, MENU_FONT_COLOR2
from math import floor
from aoslib.images import global_images
from aoslib.gui import HandlerBase, VerticalScrollBar, TextButton
from aoslib.scenes.gui.editBoxControl import EditBoxControl
from aoslib.common import collides
from aoslib import strings
from aoslib.squadEventManager import *
from pyglet import gl
from aoslib.draw import draw_quad
from shared.constants_matchmaking import *
from shared.profanityManager import *
import ast, re, os

class SquadChatLog(HandlerBase):
    messages = []
    pane_width = 0.0
    pane_height = 0.0
    pane_x = 0.0
    pane_y = 0.0
    noof_lines = 0
    noof_lines_per_page = 0
    elements = []
    text_width = 0.0
    text_height = 0.0
    media = None
    profanity_manager = None
    message_callback = None

    def __init__(self, pane_x, pane_y, pane_width, pane_height):
        self.elements = []
        self.messages = []
        self.pane_x = pane_x
        self.pane_y = pane_y
        self.pane_width = pane_width
        self.pane_height = pane_height
        line_height = self.get_line_height()
        scrollbar_width = 25
        scrollbar_button_height = 22
        edit_box_height = 24
        self.text_height = self.pane_height - edit_box_height - 5
        self.text_width = self.pane_width - scrollbar_width - 10
        self.pane_scale_x = float(self.pane_width) / float(global_images.panel_frame.width)
        self.pane_scale_y = float(self.pane_height) / float(global_images.panel_frame.height)
        self.noof_lines_per_page = int(floor(self.text_height / line_height))
        scroll_button_size = 20
        scrollbar_height = self.text_height - scroll_button_size / 2 + 2
        scrollbar_x = self.pane_x + self.pane_width - scrollbar_width / 2 - 2
        scrollbar_y = pane_y - scrollbar_height - 5
        self.scrollbar = VerticalScrollBar(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, 1, self.noof_lines_per_page, scroll_button_size)
        self.elements.append(self.scrollbar)
        button_width = 40
        button_height = 20
        x = self.pane_x + self.pane_width - button_width - 10
        y = self.pane_y - self.pane_height + 7 + button_height
        self.chat_box = EditBoxControl('', self.pane_x + 7, self.pane_y - self.pane_height + 5, self.text_width + 20, edit_box_height, center=False, empty_text=strings.CHAT_MESSAGE, draw_background=False, return_on_focus_loss=False)
        self.chat_box.on_return_callback = self.send_message_callback
        self.chat_box.font = chat_font
        self.chat_box.allow_over_typing = True
        self.elements.append(self.chat_box)
        squadEventMgr.register_callback(squadEventMgr.on_chat, self.on_chat_received)
        squadEventMgr.register_callback(squadEventMgr.on_user_join, self.on_user_joined)
        squadEventMgr.register_callback(squadEventMgr.on_user_left, self.on_user_left)
        squadEventMgr.register_callback(squadEventMgr.on_user_kicked, self.on_user_kicked)

    def on_chat_received(self, friend_id, raw_text):
        try:
            text_data = raw_text.partition(':')
            if text_data[0] == 'chat' or text_data[0] == 'in-game':
                lang_text = text_data[2].partition(':')
                language = int(lang_text[0])
                friend_name = SteamGetLobbyMemberName(friend_id)
                message = friend_name + u': ' + lang_text[2]
                colour = A2709
                if friend_id == GetUserSteamID():
                    if friend_id == SteamGetLobbyOwner():
                        colour = A2706
                    else:
                        colour = A2705
                elif friend_id == SteamGetLobbyOwner():
                    colour = A2704
                if self.profanity_manager is not None:
                    message = self.profanity_manager.sanitise_string(message)
                self.add_message(message, colour, language, text_data[0] == 'in-game')
            elif text_data[0] == 'error':
                message = text_data[2]
                data_list = ast.literal_eval(message)
                translated = strings.get_by_id(data_list[0])
                formatted = translated.format(*data_list[1])
                self.add_message(formatted, A2710)
        except:
            print 'squadChatLog - invalid chat data received'

        return

    def on_user_joined(self, friend_id):
        self.on_lobby_event_received(strings.PLAYER_JOINED_SQUAD.format(SteamGetLobbyMemberName(friend_id)))

    def on_user_left(self, friend_id, kicked=False):
        if not kicked:
            self.on_lobby_event_received(strings.PLAYER_LEFT_SQUAD.format(SteamGetLobbyMemberName(friend_id)))

    def on_user_kicked(self, friend_id):
        self.on_lobby_event_received(strings.PLAYER_KICKED_FROM_SQUAD.format(SteamGetLobbyMemberName(friend_id)))

    def send_message_callback(self, from_game=False, chat_text=None):
        if chat_text is not None:
            text = chat_text
        else:
            text = self.chat_box.text
        if text == '':
            return
        else:
            if from_game:
                prefix = 'in-game'
            else:
                prefix = 'chat'
            message = (u'{0}:{1}:').format(prefix, strings.local_language_id) + text
            SteamSendChatMessage(message)
            self.chat_box.set('')
            self.chat_box.set_focus(True)
            return

    def on_lobby_event_received(self, text):
        self.add_message(text, A2710)

    def clear_log(self):
        self.messages = []

    def add_message(self, text, colour, language=strings.LANG_ENGLISH, from_game=False):
        if not from_game and self.message_callback:
            self.message_callback(text, colour)
        split_message = split_text_to_fit_screen(chat_font, text, self.text_width, 0.0, True)
        split_message = split_message.split('\n')
        split_message = map((lambda message: (message, colour, language)), split_message)
        self.messages.extend(split_message)
        prev_scroll = self.scrollbar.scroll_pos
        is_at_scroll_base = prev_scroll == self.scrollbar.max_scroll
        max_lines = len(self.messages)
        self.scrollbar.set_max_lines(max_lines)
        if is_at_scroll_base:
            self.scrollbar.set_scroll(self.scrollbar.max_scroll)
        else:
            self.scrollbar.set_scroll(prev_scroll)
        if self.media:
            self.media.play('chat')

    def get_line_height(self):
        line_spacing = 5
        return chat_font.size + line_spacing

    def get_total_noof_lines(self):
        return len(self.messages)

    def get_lines_visible_per_page(self):
        return self.noof_lines_per_page

    def draw_background_frame(self):
        x = self.pane_x + self.pane_width / 2
        y = self.pane_y - self.pane_height / 2
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0)
        gl.glScalef(self.pane_scale_x, self.pane_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()

    def draw(self):
        self.draw_background_frame()
        draw_quad(self.pane_x + 6, self.pane_y - self.pane_height + 5, self.pane_width - 10, 22, A2703)
        for element in self.elements:
            if self.scrollbar == element and self.scrollbar.is_disabled():
                continue
            element.draw()

        top_most_line = int(self.scrollbar.scroll_pos)
        bottom_most_line = top_most_line + self.get_lines_visible_per_page()
        top_most_line = min(max(top_most_line, 0), self.get_total_noof_lines())
        bottom_most_line = min(max(bottom_most_line, 0), self.get_total_noof_lines())
        messages_to_show = self.messages[top_most_line:bottom_most_line]
        line_height = self.get_line_height()
        y = self.pane_y - line_height * (self.get_lines_visible_per_page() - len(messages_to_show))
        line_num = 0
        for msg, colour, language in messages_to_show:
            line_y = y - (line_num + 1) * line_height
            if strings.language_requires_tuffy(language):
                chat_font_tuffy.draw(msg, self.pane_x + 7, line_y, colour, False)
            else:
                chat_font.draw(msg, self.pane_x + 7, line_y, colour, False)
            line_num += 1

    def on_mouse_press(self, x, y, button, modifiers):
        for element in self.elements:
            element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_motion(self, *arg, **kw):
        for element in self.elements:
            element.on_mouse_motion(*arg, **kw)

    def on_mouse_release(self, *arg, **kw):
        for element in self.elements:
            element.on_mouse_release(*arg, **kw)

    def on_text(self, *arg, **kw):
        for element in self.elements:
            element.on_text(*arg, **kw)

    def on_text_motion(self, *arg, **kw):
        for element in self.elements:
            element.on_text_motion(*arg, **kw)

    def on_key_press(self, symbol, modifiers):
        for element in self.elements:
            element.on_key_press(symbol, modifiers)

    def on_mouse_scroll(self, x, y, dx, dy):
        over = collides(self.pane_x, self.pane_y - self.pane_height, self.pane_x + self.pane_width, self.pane_y, x, y, x, y)
        if not over:
            return
        for element in self.elements:
            element.on_mouse_scroll(x, y, dx, dy)


chatLog = SquadChatLog(56, 210, 340, 116)
