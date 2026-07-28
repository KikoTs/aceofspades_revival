from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from revival_scroll import consume_wheel_steps


class ScrollTarget:
    pass


def test_standard_wheel_notches_are_preserved():
    target = ScrollTarget()

    assert consume_wheel_steps(target, 1.0) == 1
    assert consume_wheel_steps(target, -1.0) == -1


def test_precision_wheel_packets_accumulate_to_one_step():
    target = ScrollTarget()

    assert [consume_wheel_steps(target, 0.25) for _ in range(4)] == [
        0,
        0,
        0,
        1,
    ]


def test_small_decimal_packets_do_not_lose_a_step_to_float_rounding():
    target = ScrollTarget()

    results = [consume_wheel_steps(target, 0.1) for _ in range(10)]

    assert results == [0] * 9 + [1]


def test_direction_change_discards_opposite_fractional_momentum():
    target = ScrollTarget()

    assert consume_wheel_steps(target, 0.75) == 0
    assert consume_wheel_steps(target, -0.25) == 0
    assert consume_wheel_steps(target, -0.75) == -1


def test_combined_wheel_notches_keep_their_step_count():
    target = ScrollTarget()

    assert consume_wheel_steps(target, 3.0) == 3
    assert consume_wheel_steps(target, -2.0) == -2
