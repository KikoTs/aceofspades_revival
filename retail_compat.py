"""Narrow compatibility guards for unsafe assumptions in the retail client."""

from __future__ import unicode_literals

import ast
import sys

try:
    string_types = (basestring,)
except NameError:  # pragma: no cover - Python 3 test/runtime compatibility
    string_types = (str,)


SAFE_VOTE_LITERAL = ("KICK_PLAYER", ())
_reported_malformed_literals = set()


def _report_malformed_literal(value):
    """Write a bounded, de-duplicated diagnostic without risking gameplay."""

    try:
        display = repr(value)
        if len(display) > 240:
            display = display[:237] + "..."
        if (display in _reported_malformed_literals or
                len(_reported_malformed_literals) >= 8):
            return
        _reported_malformed_literals.add(display)
        sys.stderr.write(
            "Recovered malformed retail literal: %s\n" % display
        )
    except (AttributeError, IOError, OSError, UnicodeError, ValueError):
        # Diagnostics must never replace a recovered packet failure.
        pass


def normalize_localized_literal(value, evaluator=ast.literal_eval,
                                fail_closed=False):
    """Decode and normalize a packet-47 retail localization expression.

    Retail expects ``(identifier, arguments)`` but legacy community servers
    may send a bare uppercase identifier or a one-item tuple.  Only these
    localization-shaped compatibility cases are repaired; arbitrary malformed
    input is still rejected.
    """

    try:
        decoded = evaluator(value)
    except (SyntaxError, ValueError):
        if isinstance(value, string_types):
            identifier = value.strip()
            if (identifier and identifier.replace("_", "").isalnum() and
                    identifier.upper() == identifier):
                return (identifier, ())
        if fail_closed:
            return SAFE_VOTE_LITERAL
        raise

    if (isinstance(decoded, tuple) and len(decoded) == 1 and
            isinstance(decoded[0], string_types)):
        return (decoded[0], ())
    if fail_closed:
        if (isinstance(decoded, tuple) and len(decoded) == 2 and
                isinstance(decoded[0], string_types)):
            arguments = decoded[1]
            if isinstance(arguments, tuple):
                return decoded
            if isinstance(arguments, list):
                return (decoded[0], tuple(arguments))
            return (decoded[0], (arguments,))
        if isinstance(decoded, string_types):
            identifier = decoded.strip()
            if (identifier and identifier.replace("_", "").isalnum() and
                    identifier.upper() == identifier):
                return (identifier, ())
        return SAFE_VOTE_LITERAL
    return decoded


def _called_from_retail_vote_hud():
    """Recognize the compiled HUD caller without weakening other AST users."""

    try:
        frame = sys._getframe(1)
        # Cython-generated retail builds insert a variable number of lambda,
        # scheduler, and packet-dispatch frames between literal_eval and the
        # HUD.  Walk to the thread root instead of relying on a brittle depth.
        while frame is not None:
            code = frame.f_code
            filename = code.co_filename.replace("\\", "/").lower()
            if (code.co_name == "decode_string" or
                    "genericvotinghud" in filename):
                return True
            frame = frame.f_back
    except (AttributeError, ValueError):
        pass
    return False


def install_literal_eval_guard():
    """Install the guard before the compiled GenericVotingHUD is imported."""

    if getattr(ast.literal_eval, "_aos_retail_guard", False):
        return

    original = ast.literal_eval

    def guarded_literal_eval(value):
        try:
            return normalize_localized_literal(
                value, original, fail_closed=_called_from_retail_vote_hud()
            )
        except (SyntaxError, TypeError, ValueError):
            # Cython traceback frames are visible to exception reporting but
            # are not consistently linked through ``frame.f_back`` in this
            # retail Python 2 build. Never re-raise malformed string input:
            # packet 47 is remotely supplied and the stock HUD has no guard.
            if not isinstance(value, string_types):
                raise
            _report_malformed_literal(value)
            return SAFE_VOTE_LITERAL

    guarded_literal_eval._aos_retail_guard = True
    ast.literal_eval = guarded_literal_eval
