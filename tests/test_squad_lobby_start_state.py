"""Reopening the Match Lobby must not inherit a previous Start attempt.

``MenuScene.set_menu`` keeps one cached instance per menu class, so
``initialize`` runs for the first visit only.  A reset that lives there leaves a
second visit with ``starting_game`` still set, which hides Start behind the
disabled "Waiting For Host" cancel button -- the lobby then looks alive but the
button does nothing at all.
"""
from __future__ import annotations

import ast
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "aoslib"
    / "scenes"
    / "frontend"
    / "baseSquadLobbyMenu.py"
)
SOURCE = MODULE_PATH.read_text(encoding="utf-8")
# The module is Python 2 source (print statements), so it is read as text rather
# than parsed with CPython 3's ``ast``.
LINES = SOURCE.splitlines()

WAITING_FOR_HOST = "WAITING FOR HOST"


def method_source(name):
    header = "    def %s(self" % name
    start = next(
        index for index, line in enumerate(LINES) if line.startswith(header)
    )
    end = start + 1
    while end < len(LINES) and not LINES[end].startswith("    def "):
        end += 1
    return textwrap.dedent("\n".join(LINES[start:end]))


def module_constant(name):
    """Read a module-level constant without importing the Python 2 module."""
    for line in LINES:
        if line.startswith("%s = " % name):
            return ast.literal_eval(line.split("=", 1)[1].strip())
    raise AssertionError("%s is not defined in %s" % (name, MODULE_PATH.name))


REARM_SECONDS = module_constant("ACTION_BUTTON_REARM_SECONDS")


def load_method(name, extra_globals=None):
    namespace = {
        "strings": type("strings", (), {"WAITING_FOR_HOST": WAITING_FOR_HOST}),
        "time": time,
        "ACTION_BUTTON_REARM_SECONDS": REARM_SECONDS,
    }
    namespace.update(extra_globals or {})
    exec(compile(method_source(name), str(MODULE_PATH), "exec"), namespace)
    return namespace[name]


class FakeDelayedCall:
    def __init__(self, active):
        self.is_active = active
        self.cancelled = 0

    def active(self):
        return self.is_active

    def cancel(self):
        if not self.is_active:
            raise AssertionError("an expired delayed call must not be cancelled")
        self.cancelled += 1
        self.is_active = False


class FakeServerFinder:
    def __init__(self):
        self.cancelled = 0

    def cancel(self):
        self.cancelled += 1


class FakeMenu:
    """Mirrors the class attributes the retail menu declares."""

    starting_game = True
    start_game_timer = 7
    start_game_tick_callback = None
    server_finder = None
    last_host_message = ["GAME STARTING IN {0}", 12.0]


def make_menu(callback=None, finder=None):
    menu = FakeMenu()
    menu.start_game_tick_callback = callback
    menu.server_finder = finder
    return menu


def test_reset_clears_a_stale_start_attempt():
    reset = load_method("reset_start_state")
    callback = FakeDelayedCall(active=True)
    finder = FakeServerFinder()
    menu = make_menu(callback, finder)

    reset(menu)

    assert menu.starting_game is False
    assert menu.start_game_timer == 0
    assert menu.start_game_tick_callback is None
    assert menu.server_finder is None
    assert callback.cancelled == 1
    assert finder.cancelled == 1
    assert menu.last_host_message == [WAITING_FOR_HOST, 0.0]
    assert menu._relay_lobby_start_nonce is None
    assert menu._social_join_inflight is False
    assert menu._social_join_server_id is None


def test_reset_leaves_an_already_fired_countdown_alone():
    reset = load_method("reset_start_state")
    callback = FakeDelayedCall(active=False)
    menu = make_menu(callback)

    reset(menu)

    assert callback.cancelled == 0
    assert menu.start_game_tick_callback is None


def test_reset_is_repeatable():
    reset = load_method("reset_start_state")
    menu = make_menu()

    reset(menu)
    reset(menu)

    assert menu.starting_game is False


def test_reset_does_not_mutate_the_shared_class_attribute():
    reset = load_method("reset_start_state")
    shared = FakeMenu.last_host_message
    menu = make_menu()

    reset(menu)

    assert FakeMenu.last_host_message is shared
    assert menu.last_host_message is not shared


@pytest.mark.parametrize("entry_point", ("initialize", "on_start"))
def test_every_lobby_entry_point_resets_the_start_state(entry_point):
    body = method_source(entry_point)
    assert "self.reset_start_state()" in body, (
        "%s must reset the start state; the frontend caches one menu instance "
        "per class, so a second visit would otherwise inherit it"
        % entry_point
    )


# ---------------------------------------------------------------------------
# Start, Cancel, Confirm, Join and Buy are all drawn at the same coordinates,
# so the button that replaces Start lands directly under the cursor. A second
# click of an ordinary double-click used to cancel the match the first click
# had just started, leaving the lobby idle with no server and no explanation.
# ---------------------------------------------------------------------------


class FakeButton:
    def __init__(self, visible=False, pressed=False):
        self.visible = visible
        self.pressed = pressed


def make_button_menu(**buttons):
    defaults = {
        "start_game_button": FakeButton(),
        "cancel_button": FakeButton(),
        "confirm_button": FakeButton(),
        "join_game_button": FakeButton(),
        "buy_now_button": FakeButton(),
    }
    defaults.update(buttons)
    menu = SimpleNamespace(**defaults)
    menu.action_buttons = lambda: tuple(
        getattr(menu, name) for name in (
            "start_game_button", "cancel_button", "confirm_button",
            "join_game_button", "buy_now_button",
        )
    )
    return menu


def test_a_button_that_just_appeared_swallows_the_click():
    stamp = load_method("stamp_action_buttons")
    disarm = load_method("disarm_unsettled_action_buttons")
    menu = make_button_menu()

    stamp(menu)                        # nothing visible yet
    menu.cancel_button.visible = True  # Start was pressed; Cancel took its place
    stamp(menu)
    menu.cancel_button.pressed = True  # the second half of the double-click

    disarm(menu)

    assert menu.cancel_button.pressed is False


def test_a_settled_button_still_activates():
    stamp = load_method("stamp_action_buttons")
    disarm = load_method("disarm_unsettled_action_buttons")
    menu = make_button_menu()

    menu.cancel_button.visible = True
    stamp(menu)
    menu.cancel_button.revival_armed_at = time.time() - (REARM_SECONDS + 0.5)
    menu.cancel_button.pressed = True

    disarm(menu)

    assert menu.cancel_button.pressed is True, (
        "the guard must only absorb clicks aimed at the previous button"
    )


def test_a_button_that_stays_visible_is_not_re_armed():
    stamp = load_method("stamp_action_buttons")
    menu = make_button_menu()

    menu.start_game_button.visible = True
    stamp(menu)
    armed_at = menu.start_game_button.revival_armed_at
    stamp(menu)

    assert menu.start_game_button.revival_armed_at == armed_at


def test_missing_buttons_are_tolerated_before_the_lobby_builds_them():
    stamp = load_method("stamp_action_buttons")
    disarm = load_method("disarm_unsettled_action_buttons")
    menu = make_button_menu(cancel_button=None, buy_now_button=None)

    stamp(menu)
    disarm(menu)


# ---------------------------------------------------------------------------
# Cancelling has to hand the authoritative lobby back to its idle state, or the
# next Start is rejected and the button appears to do nothing at all.
# ---------------------------------------------------------------------------


def make_cancelling_menu(starting=True):
    menu = SimpleNamespace(
        manager=object(),
        starting_game=starting,
        start_game_tick_callback=None,
        server_finder=None,
        start_game_button=None,
        _relay_lobby_start_nonce="nonce",
        _social_join_inflight=True,
        _social_join_server_id="1.2.3.4:40000",
    )
    return menu


def load_cancel(member_data, start_failed):
    return load_method(
        "do_cancel_game",
        {
            "local_host": SimpleNamespace(
                stop_active_session=lambda manager: None
            ),
            "SteamSetLobbyMemberData": lambda key, value: member_data.append(
                (key, value)
            ),
            "SteamSocialLobbyStartFailed": lambda message: start_failed.append(
                message
            ),
        },
    )


def test_cancelling_a_start_releases_the_authoritative_lobby():
    member_data = []
    start_failed = []
    do_cancel_game = load_cancel(member_data, start_failed)
    menu = make_cancelling_menu()

    do_cancel_game(menu)

    assert menu.starting_game is False
    assert menu._relay_lobby_start_nonce is None, (
        "an allocation still in flight must not launch into a cancelled lobby"
    )
    assert menu._social_join_inflight is False
    assert menu._social_join_server_id is None
    assert len(start_failed) == 1
    assert ("in-game", "0") in member_data


def test_cancelling_when_nothing_started_leaves_the_service_alone():
    member_data = []
    start_failed = []
    do_cancel_game = load_cancel(member_data, start_failed)
    menu = make_cancelling_menu(starting=False)

    do_cancel_game(menu)

    assert start_failed == []
    assert member_data == []
    assert menu._relay_lobby_start_nonce is None


def test_a_refused_endpoint_is_never_joined_again():
    mark = load_method("mark_social_server_failed")
    menu = SimpleNamespace(_failed_social_servers=set())

    mark(menu, "1.2.3.4:40000")
    mark(menu, "")

    assert menu._failed_social_servers == {"1.2.3.4:40000"}


def test_marking_recovers_when_the_lobby_inherited_the_class_default():
    mark = load_method("mark_social_server_failed")
    menu = SimpleNamespace(_failed_social_servers=frozenset())

    mark(menu, "1.2.3.4:40000")

    assert menu._failed_social_servers == {"1.2.3.4:40000"}
