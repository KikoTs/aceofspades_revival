"""Hosting must not serialize every master round-trip in front of the player.

Start Game crosses four services: reserve the social lobby, allocate a relay,
boot the bundled server, then join it.  The join code and the public listing
only need the relay allocation, so both are requested while the server is still
booting instead of adding their round-trips after it.  This file pins that
ordering, and the progress captions that tell the player which stage is running.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_HOST = PROJECT_ROOT / "local_host.py"
SOURCE = LOCAL_HOST.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function_source(name):
    node = next(
        item
        for item in TREE.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    return ast.get_source_segment(SOURCE, node) or ""


def constant(name):
    node = next(
        item.value
        for item in TREE.body
        if isinstance(item, ast.Assign)
        and any(getattr(target, "id", "") == name for target in item.targets)
    )
    return ast.literal_eval(node)


PROGRESS_NAMES = (
    "PROGRESS_RESERVING",
    "PROGRESS_ALLOCATING",
    "PROGRESS_STARTING",
    "PROGRESS_WAITING_FOR_SERVER",
    "PROGRESS_JOINING",
)

# ``START GAME`` and ``CANCEL`` are the stock captions for this 332x50 button at
# size 22.  A caption long enough to wrap drops the whole line through the font
# resizer until the glyphs stop rendering, which is what turned the hosting
# progress text into a row of blocks.
MAX_CAPTION_CHARACTERS = 14


@pytest.mark.parametrize("name", PROGRESS_NAMES)
def test_progress_captions_fit_the_action_button(name):
    caption = constant(name)
    assert len(caption) <= MAX_CAPTION_CHARACTERS, (
        "%s is %d characters; the lobby action button renders one line and "
        "longer captions lose their glyphs" % (name, len(caption))
    )
    assert caption == caption.upper(), (
        "%s should match the stock upper-case button captions" % name
    )


def test_every_stage_of_a_host_start_is_reported():
    reported = set(re.findall(r"_report_host_progress\(\s*menu,\s*(\w+)", SOURCE))
    missing = [name for name in PROGRESS_NAMES if name not in reported]
    assert not missing, (
        "these stages never reach the player, so hosting looks frozen: %s"
        % ", ".join(missing)
    )


def test_progress_reporting_cannot_break_a_launch():
    body = function_source("_report_host_progress")
    assert "except Exception" in body, (
        "progress reporting is advisory; it must never raise into the launch"
    )


def test_the_join_code_is_requested_while_the_server_boots():
    body = function_source("_connect_when_ready")
    ticket_request = body.index("request_ticket")
    readiness_arm = body.index('name="aos-local-server-ready"')
    poll_arm = body.index("clock.schedule_interval(poll_result")
    assert readiness_arm < ticket_request and poll_arm < ticket_request, (
        "the ticket must be requested alongside the readiness probe, not after"
    )


def test_the_public_listing_no_longer_gates_the_host_join():
    body = function_source("_connect_when_ready")
    assert 'social_match.connect' in body
    published = body.index("def published(")
    join = body.index("def try_join(")
    assert published < join
    # ``published`` used to call social_match.connect; the host now joins on the
    # readiness probe plus its own ticket, and the listing lands independently.
    published_body = body[published:body.index("def publish(", published)]
    assert "social_match" not in published_body, (
        "the host's own join must not wait for the public listing round-trip"
    )


def test_a_late_listing_failure_does_not_evict_a_joined_host():
    body = function_source("_connect_when_ready")
    failure = body[body.index("def publish_failed("):body.index("def join_failed(")]
    assert 'handoff["joined"]' in failure, (
        "publishing now runs beside the host's join, so a late failure must "
        "not tear down a match the host is already playing"
    )


def test_the_host_join_reports_its_own_failure():
    body = function_source("_connect_when_ready")
    assert "def join_failed(" in body
    join = body[body.index("def try_join("):]
    assert "error_callback=join_failed" in join, (
        "a failed join must not be reported to the player as a listing failure"
    )


# ---------------------------------------------------------------------------
# Our own server dying used to leave the player in the world for the full
# protocol timeout, with the lobby still advertising the dead endpoint and its
# rate-limited relay allocation still held.
# ---------------------------------------------------------------------------


def test_a_dying_server_is_noticed_instead_of_waiting_for_the_timeout():
    body = function_source("_watch_local_session")
    assert "session.is_running()" in body
    assert "stop_active_session" in body, (
        "the dead child's relay allocation must be released, not leaked"
    )
    assert "reclaim_social_lobby" in body, (
        "the lobby must become hostable again after the server dies"
    )
    assert "manager.disconnect" in body, (
        "the player should leave the dead world now, not after the ENet timeout"
    )
    assert "mark_social_server_failed" in body, (
        "the dead endpoint must not be auto-rejoined"
    )


def test_the_watchdog_is_armed_on_every_path_that_enters_a_match():
    body = function_source("_connect_when_ready")
    join = body[body.index("def try_join("):]
    # One arm for the ticketed relay join, one for the local-only session.
    assert join.count("_watch_local_session(menu, session)") == 2, (
        "both the relay join and the local-only join must be watched"
    )


def test_releasing_a_finished_session_returns_its_relay():
    body = function_source("release_finished_session")
    assert "stop_active_session" in body
    assert "server_id" in body, (
        "callers need the endpoint that just died so they can blacklist it"
    )


def test_reclaiming_uses_the_only_verb_that_resets_the_lobby():
    body = function_source("reclaim_social_lobby")
    assert "SteamSocialLobbyStartFailed" in body, (
        "the service exposes no match-over verb; start_failed is the reset"
    )
