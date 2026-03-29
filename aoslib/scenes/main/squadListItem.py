from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.main.matchSettings import get_game_rules_and_values_list
from aoslib import strings
from aoslib.text import draw_text_with_alignment_and_size_validation
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import TEXT_BACKGROUND_SPACING
from shared.steam import SteamGetLobbyData, SteamGetLobbyPing, SteamGetFriendPersonaName, SteamGetLobbyMembers

class SquadListItem(ListPanelItemBase):
    friend_members = []

    def initialize(self, lobby_id):
        super(SquadListItem, self).initialize()
        self.lobby_id = lobby_id
        self.ping = None
        self.refresh()
        if self.name is None or self.name == '':
            self.name = 'random name ' + str(len(self.friend_members))
            self.noof_members_text = '0/8'
        return

    def is_same_item(self, item):
        if item is None:
            return False
        else:
            return self.lobby_id == item.lobby_id

    def is_squad_full(self):
        return int(self.noof_members) >= int(self.max_noof_members)

    def refresh(self):
        self.name = SteamGetLobbyData(self.lobby_id, 'Name')
        self.noof_members = SteamGetLobbyData(self.lobby_id, 'NumMembers')
        self.max_noof_members = SteamGetLobbyData(self.lobby_id, 'MAX_PLAYERS')
        self.noof_members_text = ('{0}/{1}').format(self.noof_members, self.max_noof_members)
        self.friend_members = SteamGetLobbyMembers(self.lobby_id)
        self.game_info = get_game_rules_and_values_list(self.lobby_id)
        self.ping = SteamGetLobbyPing(self.lobby_id)

    def is_open(self):
        return self.name != '' and self.name != None

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        text_spacing = 15
        half_width = self.width / 2
        name_width = half_width - text_spacing
        name_x = self.x1 + TEXT_BACKGROUND_SPACING
        players_width = 25
        players_x = self.x1 + self.width - text_spacing - players_width
        friends_width = half_width - players_width - text_spacing * 3
        friends_x = players_x - friends_width - text_spacing
        ping_width = half_width - friends_width - text_spacing * 3
        ping_x = friends_x - ping_width - text_spacing
        text_colour = MENU_FONT_COLOR
        noof_friends = len(self.friend_members)
        text = None if len(self.friend_members) == 0 else (u'({0} {1})').format(noof_friends, strings.FRIENDS if noof_friends > 1 else strings.FRIEND)
        draw_text_with_alignment_and_size_validation(self.name, name_x, self.y1, name_width, self.height, text_colour, self.font, alignment_x='left', alignment_y='center')
        if text is not None:
            draw_text_with_alignment_and_size_validation(text, friends_x, self.y1, friends_width, self.height, (146,
                                                                                                                241,
                                                                                                                141,
                                                                                                                255), self.font, alignment_y='center')
        draw_text_with_alignment_and_size_validation(self.noof_members_text, players_x, self.y1, players_width, self.height, text_colour, self.font, alignment_y='center')
        if self.ping:
            draw_text_with_alignment_and_size_validation(str(self.ping), ping_x, self.y1, ping_width, self.height, text_colour, self.font, alignment_y='center')
        return

    def draw(self, colour):
        if not self.enabled:
            return
        super(SquadListItem, self).draw(colour)
