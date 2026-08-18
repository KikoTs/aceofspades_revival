"""A service outage must not read as "you are signed out".

The master answers ``POST /api/social/friends`` with HTTP 503
``auth_unavailable`` / "Authentication is temporarily unavailable" while its
auth dependency is down.  Echoing that verbatim sends players off to re-login
over an outage they cannot do anything about, so the client rewords 5xx and
transport failures and keeps the raw text only for errors the player can act on.
"""
from __future__ import annotations

import pytest

from revival_api import RevivalApiError, player_facing_message


def test_a_service_outage_reassures_instead_of_blaming_the_session():
    message = player_facing_message(
        RevivalApiError("Authentication is temporarily unavailable.",
                        "auth_unavailable", 503)
    )

    assert "temporarily unavailable" in message
    assert "sign-in is still fine" in message.lower()
    assert "Authentication is temporarily unavailable." not in message


@pytest.mark.parametrize("status", (500, 502, 503, 504))
def test_every_server_side_failure_is_reworded(status):
    message = player_facing_message(
        RevivalApiError("Authentication is temporarily unavailable.",
                        "auth_unavailable", status)
    )
    assert "sign-in is still fine" in message.lower()


def test_a_transport_failure_points_at_the_connection():
    message = player_facing_message(
        RevivalApiError("Could not reach the Revival service: timeout",
                        "network_error")
    )
    assert "connection" in message.lower()


def test_a_real_sign_in_problem_still_asks_for_a_sign_in():
    message = player_facing_message(
        RevivalApiError("Sign in to use Friends.", "authentication_required", 401)
    )
    assert "sign in" in message.lower()


def test_an_actionable_rejection_keeps_the_services_own_wording():
    message = player_facing_message(
        RevivalApiError("No exact player match was found.", "player_not_found", 404)
    )
    assert message == "No exact player match was found."


def test_a_bare_exception_still_produces_something_readable():
    assert player_facing_message(RuntimeError("boom"))
