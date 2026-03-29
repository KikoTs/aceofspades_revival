import json, urllib
from twisted.web.client import getPage
from shared.constants import BLITZ_DEV
SCORE_SERVER_URL = 'http://localhost:3000/api'
SCORE_SERVER_CONNECTION_TIMEOUT = 5.0

class ScoreManager(object):

    def __init__(self):
        self.request_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.request_profile_callback = None
        self.request_leaderboard_callback = None
        return

    def request_profile(self, steam_id):
        try:
            fields = {'steamid': steam_id}
            data = urllib.urlencode(fields)
            request = getPage(SCORE_SERVER_URL + '/profile', method='POST', postdata=data, headers=self.request_headers, timeout=SCORE_SERVER_CONNECTION_TIMEOUT)
            request.addCallbacks(self.__request_profile_callback, self.__request_profile_error_callback)
        except:
            import traceback
            print traceback.format_exc()

    def set_request_profile_callback(self, callback):
        self.request_profile_callback = callback

    def clear_request_profile_callback(self):
        self.request_profile_callback = None
        return

    def __request_profile_callback(self, result):
        if result:
            profile = None
            try:
                profile = json.loads(result)
                if self.request_profile_callback:
                    self.request_profile_callback(profile)
            except:
                import traceback
                print traceback.format_exc()

        return

    def __request_profile_error_callback(self, result):
        if self.request_profile_callback:
            self.request_profile_callback(None)
        return

    def request_global_leaderboard(self, stat_id_list, sort_stat_id):
        self.__request_leaderboard(stat_id_list, sort_stat_id)

    def request_local_leaderboard(self, stat_id_list, sort_stat_id, steam_id):
        self.__request_leaderboard(stat_id_list, sort_stat_id, steam_id=steam_id, noof_results=10)

    def request_friend_leaderboard(self, stat_id_list, sort_stat_id, friend_list):
        self.__request_leaderboard(stat_id_list, sort_stat_id, friend_list=friend_list)

    def __request_leaderboard(self, stat_id_list, sort_stat_id, steam_id=None, noof_results=None, friend_list=None):
        try:
            fields = {'sortid': sort_stat_id, 'noof_stats': (len(stat_id_list)), 'statid': stat_id_list}
            if steam_id:
                fields['steamid'] = steam_id
            if noof_results:
                fields['noof_results'] = noof_results
            if friend_list:
                fields['noof_friends'] = len(friend_list)
                fields['friend'] = friend_list
            data = urllib.urlencode(fields, True)
            request = getPage(SCORE_SERVER_URL + '/leaderboard', method='POST', postdata=data, headers=self.request_headers, timeout=SCORE_SERVER_CONNECTION_TIMEOUT)
            request.addCallbacks(self.__request_leaderboard_callback, self.__request_leaderboard_error_callback)
        except:
            import traceback
            print traceback.format_exc()

    def set_request_leaderboard_callback(self, callback):
        self.request_leaderboard_callback = callback

    def clear_request_leaderboard_callback(self):
        self.request_leaderboard_callback = None
        return

    def __request_leaderboard_callback(self, result):
        if result:
            leaderboard = None
            try:
                leaderboard = json.loads(result)
                if self.request_leaderboard_callback:
                    self.request_leaderboard_callback(leaderboard)
            except:
                import traceback
                print traceback.format_exc()

        return

    def __request_leaderboard_error_callback(self, result):
        if self.request_leaderboard_callback:
            self.request_leaderboard_callback(None)
        return
