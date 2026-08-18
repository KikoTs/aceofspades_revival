# -*- coding: utf-8 -*-
"""Native Revival friends, requests, invitations, and invite picker UI."""
from __future__ import absolute_import

import json
import time

from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.gui import Label
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.panelBase import PanelBase
from aoslib.scenes.gui.editBoxControl import EditBoxControl
from aoslib.scenes.gui.messageBox import (
    BUTTONS_OK,
    BUTTONS_YES_NO,
    DIALOG_WITH_BUTTONS,
    MessageBox,
)
from aoslib.scenes.main.socialListItem import SocialListItem
from aoslib.text import ALDO_FONT, START_FONT
from shared.steam import (
    SteamDeclineLobbyInvite,
    SteamFindRevivalPlayer,
    SteamFriendAction,
    SteamGetCurrentLobby,
    SteamGetLobbyMembers,
    SteamGetSocialInvitations,
    SteamGetSocialSnapshot,
    SteamInviteFriend,
    SteamIsSocialAvailable,
    SteamJoinLobby,
    SteamLeaveLobby,
)

VIEW_FRIENDS = "friends"
VIEW_REQUESTS = "requests"
VIEW_INVITES = "invites"
MESSAGE_NONE = 0
MESSAGE_ERROR = 1
MESSAGE_ABANDON = 2

LEFT_X = 56
LEFT_WIDTH = 340
RIGHT_X = 401
RIGHT_WIDTH = 340
CONTENT_TOP = 505
CONTENT_BOTTOM = 144
TAB_HEIGHT = 34
SEARCH_HEIGHT = 34
SEARCH_BOTTOM = 428
LIST_TOP = 418
LIST_HEIGHT = LIST_TOP - CONTENT_BOTTOM
ACTION_WIDTH = 162
ACTION_HEIGHT = 48


def _text(value):
    if value is None:
        return u""
    try:
        return unicode(value)
    except Exception:
        return u""


def _error_text(error):
    try:
        from revival_api import player_facing_message
    except ImportError:
        message = getattr(error, "message", None) or _text(error)
        return message or u"The social service could not complete this action."
    return player_facing_message(error)


class FriendsMenu(ListPreviewMenuBase):
    title = u"FRIENDS"

    def initialize(self):
        ListPreviewMenuBase.initialize(self, self.title)
        self.list_panel = ListPanelBase(self.manager)
        self.details_panel = PanelBase(self.manager)
        self.search_box = EditBoxControl(
            u"", LEFT_X, SEARCH_BOTTOM, 236, SEARCH_HEIGHT, center=False,
            empty_text=u"Username / nickname / profile ID",
            max_characters=64, return_on_focus_loss=False,
        )
        self.details_name = Label(
            u"", x=RIGHT_X + 20, y=445, width=RIGHT_WIDTH - 40,
            height=42, anchor_x='left', anchor_y='top',
            font_name=ALDO_FONT, font_size=20,
            color=(224, 215, 164, 255),
        )
        self.details_meta = Label(
            u"", x=RIGHT_X + 20, y=402, width=RIGHT_WIDTH - 40,
            height=82, anchor_x='left', anchor_y='top',
            font_name=START_FONT, font_size=12,
            color=(205, 203, 181, 255),
        )
        self.status_label = Label(
            u"", x=RIGHT_X + 20, y=184, width=RIGHT_WIDTH - 40,
            height=32, anchor_x='left', anchor_y='top',
            font_name=START_FONT, font_size=10,
            color=(154, 158, 130, 255),
        )
        self.message_box = MessageBox(400, 300)
        self.message_box.set_buttons_callback(
            self.message_box_button_one_pressed,
            self.message_box_button_two_pressed,
        )
        self.view = VIEW_FRIENDS
        self.invite_picker = False
        self.return_menu = None
        self.refresh_at = 0.0
        self.snapshot_key = None
        self.pending_join = None
        self.message_type = MESSAGE_NONE
        self.status_text = u""

    def on_start(self, invite_picker=False, return_menu=None, **kw):
        self.invite_picker = bool(invite_picker)
        self.return_menu = return_menu
        self.view = VIEW_FRIENDS if self.invite_picker else self.view
        self.pending_join = None
        self.message_type = MESSAGE_NONE
        self.elements = [self.navigation_bar, self.list_panel,
                         self.details_panel]
        if not self.invite_picker:
            self.elements.append(self.search_box)
        self.buttons = []
        tab_spacing = 4
        tab_width = (LEFT_WIDTH - tab_spacing * 2) / 3.0
        friends_width = LEFT_WIDTH if self.invite_picker else tab_width
        self.friends_button = self.create_button(
            u"ONLINE FRIENDS" if self.invite_picker else u"FRIENDS",
            LEFT_X, CONTENT_TOP, friends_width, TAB_HEIGHT, 14,
            self.show_friends)
        self.requests_button = self.create_button(
            u"REQUESTS", LEFT_X + tab_width + tab_spacing, CONTENT_TOP,
            tab_width, TAB_HEIGHT, 14, self.show_requests)
        self.invites_button = self.create_button(
            u"INVITES", LEFT_X + (tab_width + tab_spacing) * 2,
            CONTENT_TOP, tab_width, TAB_HEIGHT, 14, self.show_invites)
        self.add_button = self.create_button(
            u"ADD", LEFT_X + 236 + 4, SEARCH_BOTTOM + SEARCH_HEIGHT,
            100, SEARCH_HEIGHT, 14, self.add_exact_player)
        self.primary_button = self.create_button(
            u"JOIN", RIGHT_X + 4, 310, ACTION_WIDTH, ACTION_HEIGHT, 18,
            self.primary_action)
        self.secondary_button = self.create_button(
            u"INVITE", RIGHT_X + 174, 310, ACTION_WIDTH, ACTION_HEIGHT,
            18, self.secondary_action)
        self.remove_button = self.create_button(
            u"REMOVE", RIGHT_X + 4, 254, ACTION_WIDTH, ACTION_HEIGHT, 18,
            self.remove_action)
        self.block_button = self.create_button(
            u"BLOCK", RIGHT_X + 174, 254, ACTION_WIDTH, ACTION_HEIGHT, 18,
            self.block_action)
        if self.invite_picker:
            self.requests_button.visible = False
            self.invites_button.visible = False
            self.add_button.visible = False
        self.details_panel.initialise_ui(
            u"INVITE A FRIEND" if self.invite_picker else u"FRIEND DETAILS",
            RIGHT_X, CONTENT_TOP, RIGHT_WIDTH,
            CONTENT_TOP - CONTENT_BOTTOM, has_header=True,
        )
        self.details_panel.center_header_text = True
        self.list_panel.initialise_ui(
            u"ONLINE FRIENDS" if self.invite_picker else u"FRIENDS",
            LEFT_X, LIST_TOP if not self.invite_picker else 461,
            LEFT_WIDTH,
            LIST_HEIGHT if not self.invite_picker else 461 - CONTENT_BOTTOM,
            row_height=34, has_header=False,
        )
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.message_box.set_visible(False)
        # Modal dialogs must render above every control.
        self.elements.append(self.message_box)
        self.snapshot_key = None
        self.refresh_at = 0.0
        self._refresh(True)

    def draw(self):
        ListPreviewMenuBase.draw(self)
        if not self.message_box.visible:
            self.details_name.draw()
            self.details_meta.draw()
            self.status_label.draw()

    def on_stop(self):
        self.search_box.set_focus(False)

    def open_parent_menu(self):
        if self.return_menu is not None:
            self.parent.set_menu(
                self.return_menu, back=True, in_game_menu=self.in_game_menu)
        elif self.in_game_menu:
            from aoslib.scenes.ingame_menus.escapeMenu import EscapeMenu
            self.parent.set_menu(EscapeMenu, back=True, in_game_menu=True)
        else:
            from aoslib.scenes.frontend.selectMenu import SelectMenu
            self.parent.set_menu(SelectMenu, back=True)

    def update(self, dt):
        ListPreviewMenuBase.update(self, dt)
        if time.time() >= self.refresh_at:
            self._refresh(False)
            self.refresh_at = time.time() + 0.5

    def _snapshot(self):
        snapshot = SteamGetSocialSnapshot()
        if not isinstance(snapshot, dict):
            snapshot = {}
        snapshot["invitations"] = SteamGetSocialInvitations()
        return snapshot

    def _records(self, snapshot):
        friends = [row for row in snapshot.get("friends") or []
                   if isinstance(row, dict)]
        if self.view == VIEW_REQUESTS:
            return [("request", row) for row in friends
                    if row.get("friendship_status") == "pending"]
        if self.view == VIEW_INVITES:
            return [("invite", row) for row in snapshot.get("invitations") or []
                    if isinstance(row, dict)]
        accepted = [row for row in friends
                    if row.get("friendship_status") == "accepted"]
        if self.invite_picker:
            current = SteamGetCurrentLobby()
            members = set(SteamGetLobbyMembers(current)) if current else set()
            accepted = [row for row in accepted
                        if row.get("presence") != "offline"
                        and int(row.get("legacy_id") or 0) not in members]
        return [("friend", row) for row in accepted]

    def _record_key(self, kind, record):
        if kind == "invite":
            return u"invite:%s" % _text(record.get("id") or record.get("lobby_id"))
        return u"%s:%s" % (kind, _text(record.get("legacy_id")))

    def _record_name(self, kind, record):
        if kind == "invite":
            inviter = record.get("inviter") or {}
            return u"%s  -  invited by %s" % (
                _text(record.get("lobby_name") or u"Lobby"),
                _text(inviter.get("nickname") or u"Unknown"),
            )
        nickname = _text(record.get("nickname") or record.get("username") or
                         record.get("legacy_id"))
        if kind == "request":
            direction = _text(record.get("direction")).upper()
            return u"%s  [%s]" % (nickname, direction)
        presence = _text(record.get("presence") or u"offline").upper()
        lobby = u"  [IN LOBBY]" if record.get("current_lobby_id") else u""
        return u"%s  -  %s%s" % (nickname, presence, lobby)

    def _refresh(self, force):
        snapshot = self._snapshot()
        records = self._records(snapshot)
        key = json.dumps(records, sort_keys=True, separators=(",", ":"))
        if not force and key == self.snapshot_key:
            self._update_buttons()
            return
        selected = self.list_panel.get_selected_item()
        selected_uid = selected.uid if selected is not None else None
        del self.list_panel.rows[:]
        for kind, record in records:
            row = SocialListItem(
                self._record_name(kind, record),
                self._record_key(kind, record), kind, record,
            )
            self.list_panel.rows.append(row)
        self.list_panel.recreate_scrollbar()
        if selected_uid is not None:
            self.list_panel.select_row_with_uid(selected_uid)
        if self.list_panel.get_selected_item() is None and self.list_panel.rows:
            self.list_panel.select_row(self.list_panel.rows[0])
        self.snapshot_key = key
        self._update_buttons()

    def _set_view(self, view):
        self.view = view
        self.friends_button.set_constant_glow(view == VIEW_FRIENDS)
        self.requests_button.set_constant_glow(view == VIEW_REQUESTS)
        self.invites_button.set_constant_glow(view == VIEW_INVITES)
        self.snapshot_key = None
        self._refresh(True)

    def show_friends(self):
        self._set_view(VIEW_FRIENDS)

    def show_requests(self):
        if not self.invite_picker:
            self._set_view(VIEW_REQUESTS)

    def show_invites(self):
        if not self.invite_picker:
            self._set_view(VIEW_INVITES)

    def on_row_selected(self, index, row):
        self._update_buttons()

    def _selected(self):
        return self.list_panel.get_selected_item()

    def _set_button(self, button, text, enabled):
        button.set_text(text)
        button.enabled = bool(enabled) and SteamIsSocialAvailable()
        button.visible = True

    def _update_details(self, row):
        if self.invite_picker:
            panel_title = u"INVITE A FRIEND"
        elif self.view == VIEW_REQUESTS:
            panel_title = u"FRIEND REQUEST"
        elif self.view == VIEW_INVITES:
            panel_title = u"LOBBY INVITATION"
        else:
            panel_title = u"FRIEND DETAILS"
        self.details_panel.title = panel_title

        if row is None:
            empty_text = {
                VIEW_FRIENDS: u"No friend selected",
                VIEW_REQUESTS: u"No request selected",
                VIEW_INVITES: u"No invitation selected",
            }.get(self.view, u"Nothing selected")
            self.details_name.text = empty_text
            self.details_meta.text = (
                u"Select an entry on the left to see the available actions."
            )
        else:
            record = row.record
            if row.kind == "invite":
                inviter = record.get("inviter") or {}
                self.details_name.text = _text(
                    record.get("lobby_name") or u"Lobby invitation")
                self.details_meta.text = u"Invited by: %s\nLobby ID: %s" % (
                    _text(inviter.get("nickname") or u"Unknown"),
                    _text(record.get("lobby_id") or u"Unknown"),
                )
            else:
                self.details_name.text = _text(
                    record.get("nickname") or record.get("username") or
                    record.get("legacy_id"))
                detail_lines = []
                if row.kind == "request":
                    detail_lines.append(
                        u"%s friend request" %
                        _text(record.get("direction") or u"pending").title())
                else:
                    detail_lines.append(
                        u"Status: %s" %
                        _text(record.get("presence") or u"offline").title())
                public_id = record.get("public_id")
                if public_id:
                    detail_lines.append(u"Profile ID: %s" % _text(public_id))
                if record.get("current_lobby_id"):
                    detail_lines.append(u"Currently playing in a lobby")
                self.details_meta.text = u"\n".join(detail_lines)

        if SteamIsSocialAvailable():
            self.status_label.text = self.status_text or (
                u"Friends and lobby presence are synchronized."
            )
        else:
            self.status_label.text = (
                u"Social service unavailable. Local play still works."
            )

    def _update_buttons(self):
        row = self._selected()
        self.requests_button.enabled = not self.invite_picker
        self.invites_button.enabled = not self.invite_picker
        self.search_box.enabled = not self.invite_picker and not self.message_box.visible
        self.add_button.enabled = self.search_box.enabled and SteamIsSocialAvailable()
        self.friends_button.set_constant_glow(self.view == VIEW_FRIENDS)
        self.requests_button.set_constant_glow(self.view == VIEW_REQUESTS)
        self.invites_button.set_constant_glow(self.view == VIEW_INVITES)
        for button in (self.primary_button, self.secondary_button,
                       self.remove_button, self.block_button):
            button.enabled = False
            button.visible = False
        self._update_details(row)
        if row is None:
            return
        record = row.record
        if row.kind == "request":
            incoming = record.get("direction") == "incoming"
            self._set_button(self.primary_button, u"ACCEPT", incoming)
            self._set_button(self.secondary_button, u"DECLINE", incoming)
            self._set_button(self.remove_button, u"CANCEL", not incoming)
            self._set_button(self.block_button, u"BLOCK", True)
        elif row.kind == "invite":
            self._set_button(self.primary_button, u"ACCEPT", True)
            self._set_button(self.secondary_button, u"DECLINE", True)
            self.remove_button.enabled = False
            self.block_button.enabled = False
        else:
            can_join = bool(record.get("current_lobby_id"))
            can_invite = bool(SteamGetCurrentLobby()) and record.get("presence") != "offline"
            if self.invite_picker:
                self._set_button(self.primary_button, u"INVITE", can_invite)
                self.secondary_button.enabled = False
                self.remove_button.enabled = False
                self.block_button.enabled = False
            else:
                self._set_button(self.primary_button, u"JOIN", can_join)
                self._set_button(self.secondary_button, u"INVITE", can_invite)
                self._set_button(self.remove_button, u"REMOVE", True)
                self._set_button(self.block_button, u"BLOCK", True)

    def add_exact_player(self):
        query = _text(self.search_box.value).strip()
        if not query:
            self._show_error(u"Enter an exact username, nickname, or profile ID.")
            return

        def found(result):
            player = (result or {}).get("player")
            if not player:
                self._show_error(u"No exact player match was found.")
                return
            SteamFriendAction(
                "request", player.get("legacy_id"),
                lambda response: self._action_finished(u"Friend request sent."),
                self._show_error,
            )

        SteamFindRevivalPlayer(query, found, self._show_error)

    def primary_action(self):
        row = self._selected()
        if row is None:
            return
        if row.kind == "request":
            self._friend_action("accept", row.record)
        elif row.kind == "invite":
            self._request_join(row.record.get("lobby_id"), row.record.get("id"))
        elif self.invite_picker:
            self._invite(row.record)
        else:
            self._request_join(row.record.get("current_lobby_id"))

    def secondary_action(self):
        row = self._selected()
        if row is None:
            return
        if row.kind == "request":
            self._friend_action("decline", row.record)
        elif row.kind == "invite":
            self._decline_invite(row.record)
        elif row.kind == "friend":
            self._invite(row.record)

    def remove_action(self):
        row = self._selected()
        if row is None:
            return
        self._friend_action("remove", row.record)

    def block_action(self):
        row = self._selected()
        if row is None or row.kind == "invite":
            return
        self._friend_action("block", row.record)

    def _friend_action(self, action, record):
        SteamFriendAction(
            action, record.get("legacy_id"),
            lambda response: self._action_finished(u"Social list updated."),
            self._show_error,
        )

    def _invite(self, record):
        SteamInviteFriend(
            record.get("legacy_id"),
            lambda response: self._action_finished(u"Lobby invitation sent."),
            self._show_error,
        )

    def _decline_invite(self, record):
        SteamDeclineLobbyInvite(
            record.get("lobby_id"), record.get("id"),
            lambda response: self._action_finished(u"Invitation declined."),
            self._show_error,
        )

    def _request_join(self, lobby_id, invitation_id=None):
        try:
            lobby_id = int(lobby_id or 0)
        except Exception:
            lobby_id = 0
        if not lobby_id:
            self._show_error(u"This lobby is no longer available.")
            return
        current = SteamGetCurrentLobby()
        abandon = self.in_game_menu or (current and current != lobby_id)
        if abandon:
            self.pending_join = (lobby_id, invitation_id)
            self._show_message(
                MESSAGE_ABANDON,
                u"Leave the current lobby or hosted match and join this lobby?",
                BUTTONS_YES_NO,
            )
            return
        self._join(lobby_id, invitation_id)

    def _join(self, lobby_id, invitation_id=None):
        # SteamJoinLobby accepts authoritative invites even without passing the
        # invitation UUID; the backend locates the pending invite atomically.
        SteamJoinLobby(self._joined, self._join_failed, lobby_id)

    def _leave_then_join(self, lobby_id, invitation_id):
        try:
            import local_host
            local_host.stop_active_session(self.manager)
        except Exception:
            pass
        if self.in_game_menu:
            try:
                game_scene = self.manager.game_scene
                if game_scene is not None:
                    game_scene.disconnect()
            except Exception:
                pass
        if SteamGetCurrentLobby():
            SteamLeaveLobby(
                lambda result: self._join(lobby_id, invitation_id),
                self._show_error,
            )
        else:
            self._join(lobby_id, invitation_id)

    def _joined(self, lobby_id):
        from social_lobby_navigation import open_social_lobby
        if self.in_game_menu:
            open_social_lobby(self.manager, as_scene=True)
        else:
            open_social_lobby(self.manager, parent=self.parent)

    def _join_failed(self, error):
        self._show_error(error)

    def _action_finished(self, message):
        self.status_text = _text(message)
        self.snapshot_key = None
        self.refresh_at = 0.0

    def _show_error(self, error):
        self._show_message(MESSAGE_ERROR, _error_text(error), BUTTONS_OK)

    def _show_message(self, message_type, text, buttons):
        self.message_type = message_type
        for element in self.elements:
            if element is not self.message_box:
                element.enabled = False
        self.message_box.set_dialog_message_type(DIALOG_WITH_BUTTONS, buttons, text)
        self.message_box.set_visible(True)

    def _hide_message(self):
        self.message_type = MESSAGE_NONE
        self.message_box.set_visible(False)
        for element in self.elements:
            element.enabled = True
        self._update_buttons()

    def message_box_button_one_pressed(self):
        message_type = self.message_type
        pending = self.pending_join
        self.pending_join = None
        self._hide_message()
        if message_type == MESSAGE_ABANDON and pending is not None:
            self._leave_then_join(pending[0], pending[1])

    def message_box_button_two_pressed(self):
        self.pending_join = None
        self._hide_message()


__all__ = ["FriendsMenu"]
