from shared.steam import SteamRegisterLobbyChatCallback, SteamRegisterLobbyUpdateCallback, SteamRegisterLobbyJoinRequestCallback, SteamRegisterLobbyDataChangedCallback, SteamGetCurrentLobby
from shared.steam import SteamAmITheLobbyOwner, SteamSetLobbyData, SteamGetPersonaName, SteamLeaveLobby, GetUserSteamID, SteamGetLobbyOwner
import ast

class SquadEventManager:
    on_chat = []
    on_user_join = []
    on_user_left = []
    on_user_kicked = []
    on_invite_received = []
    on_data_changed = []
    kicked_users = []

    def __init__(self):
        SteamRegisterLobbyChatCallback(self.on_chat_received_callback)
        SteamRegisterLobbyUpdateCallback(self.on_user_joined_callback, self.on_user_left_callback, self.on_user_kicked_callback)
        SteamRegisterLobbyJoinRequestCallback(self.on_invite_received_callback)
        SteamRegisterLobbyDataChangedCallback(self.on_data_changed_callback)
        self.register_callback(self.on_user_left, self.__on_user_left)

    def register_callback(self, list, callback):
        self.unregister_callback(list, callback)
        list.append(callback)

    def unregister_callback(self, list, callback):
        try:
            list.remove(callback)
        except:
            pass

    def call_callback(self, list, *arg, **kw):
        for callback in list:
            callback(*arg, **kw)

    def on_chat_received_callback(self, friend_id, text):
        try:
            text_data = text.partition(':')
            if text_data[2] == '':
                return
            if text_data[0] == 'cmd':
                if friend_id == SteamGetLobbyOwner():
                    data_list = ast.literal_eval(text_data[2])
                    command = data_list[0]
                    parameters = data_list[1]
                    if command == 'KICK_PLAYER':
                        kick_id = int(parameters[0])
                        self.on_user_kicked_callback(kick_id)
                        if kick_id == GetUserSteamID() and not SteamAmITheLobbyOwner():
                            SteamLeaveLobby()
            self.call_callback(self.on_chat, friend_id, text)
        except:
            print 'squadEventManager - invalid chat data received'

    def on_user_joined_callback(self, friend_id):
        self.call_callback(self.on_user_join, friend_id)

    def on_user_left_callback(self, friend_id):
        if friend_id in self.kicked_users:
            self.kicked_users.remove(friend_id)
            self.call_callback(self.on_user_left, friend_id, True)
        else:
            self.call_callback(self.on_user_left, friend_id)

    def on_user_kicked_callback(self, friend_id):
        self.kicked_users.append(friend_id)
        self.call_callback(self.on_user_kicked, friend_id)

    def on_invite_received_callback(self, lobby_id):
        if SteamGetCurrentLobby() != lobby_id:
            self.call_callback(self.on_invite_received, lobby_id)

    def on_data_changed_callback(self, lobby_id, success):
        self.call_callback(self.on_data_changed, lobby_id, success)

    def __on_user_left(self, friend_id, kicked=False):
        pass


squadEventMgr = SquadEventManager()
