"""Unit tests for LatencyBuffer (Requirements 10.1–10.4)."""

import pytest
from env.latency_buffer import LatencyBuffer


MSG_DIM = 16
ZERO = [0.0] * MSG_DIM


def make_msg(val: float) -> list[float]:
    return [val] * MSG_DIM


class TestTauZero:
    """τ=0: push then pop returns the current message immediately (no delay)."""

    def test_push_pop_returns_same_message(self):
        buf = LatencyBuffer(tau=0)
        msg = make_msg(1.0)
        buf.push(msg)
        assert buf.pop() == msg

    def test_multiple_sequential_cycles(self):
        buf = LatencyBuffer(tau=0)
        for i in range(5):
            msg = make_msg(float(i))
            buf.push(msg)
            assert buf.pop() == msg

    def test_message_returned_unmodified(self):
        buf = LatencyBuffer(tau=0)
        msg = [float(i) for i in range(MSG_DIM)]
        buf.push(msg)
        assert buf.pop() == msg


class TestTauOne:
    """τ=1: first pop returns zeros, second pop (after push) returns message."""

    def test_first_pop_before_push_returns_zero(self):
        buf = LatencyBuffer(tau=1)
        assert buf.pop() == ZERO

    def test_first_pop_after_one_push_returns_zero(self):
        buf = LatencyBuffer(tau=1)
        buf.push(make_msg(1.0))
        assert buf.pop() == ZERO

    def test_second_pop_after_two_pushes_returns_first_message(self):
        buf = LatencyBuffer(tau=1)
        msg1 = make_msg(1.0)
        msg2 = make_msg(2.0)
        buf.push(msg1)
        buf.push(msg2)
        assert buf.pop() == msg1

    def test_sequential_push_pop_cycle(self):
        buf = LatencyBuffer(tau=1)
        msg_a = make_msg(10.0)
        msg_b = make_msg(20.0)
        buf.push(msg_a)
        buf.push(msg_b)
        assert buf.pop() == msg_a
        buf.push(make_msg(30.0))
        assert buf.pop() == msg_b


class TestTauThree:
    """τ=3: first 3 pops return zeros, 4th pop returns first pushed message."""

    def test_first_three_pops_return_zero_vectors(self):
        buf = LatencyBuffer(tau=3)
        for _ in range(3):
            buf.push(make_msg(1.0))
            assert buf.pop() == ZERO

    def test_fourth_pop_returns_first_message(self):
        buf = LatencyBuffer(tau=3)
        first_msg = make_msg(42.0)
        buf.push(first_msg)
        buf.push(make_msg(2.0))
        buf.push(make_msg(3.0))
        buf.push(make_msg(4.0))
        assert buf.pop() == first_msg

    def test_fifo_ordering_maintained(self):
        buf = LatencyBuffer(tau=3)
        messages = [make_msg(float(i)) for i in range(6)]
        # Push first 4 to fill buffer
        for i in range(4):
            buf.push(messages[i])
        # Now pop should return messages[0], then push+pop for subsequent
        assert buf.pop() == messages[0]
        buf.push(messages[4])
        assert buf.pop() == messages[1]
        buf.push(messages[5])
        assert buf.pop() == messages[2]


class TestEarlyEpisodeZeroVectors:
    """Before buffer fills, pop returns zero vectors."""

    def test_pop_before_any_push_returns_zero(self):
        for tau in [1, 2, 5, 10]:
            buf = LatencyBuffer(tau=tau)
            assert buf.pop() == ZERO, f"Failed for tau={tau}"

    def test_exactly_tau_pushes_still_returns_zero(self):
        tau = 4
        buf = LatencyBuffer(tau=tau)
        for i in range(tau):
            buf.push(make_msg(float(i)))
        # After exactly tau pushes, buffer has tau items but needs tau+1 to be full
        assert buf.pop() == ZERO

    def test_tau_plus_one_pushes_returns_first_message(self):
        tau = 4
        buf = LatencyBuffer(tau=tau)
        first_msg = make_msg(99.0)
        buf.push(first_msg)
        for i in range(tau):
            buf.push(make_msg(float(i)))
        assert buf.pop() == first_msg


class TestClearMethod:
    """clear() resets buffer so next pop returns zero vector again."""

    def test_clear_on_full_buffer_resets_to_zero(self):
        buf = LatencyBuffer(tau=1)
        buf.push(make_msg(1.0))
        buf.push(make_msg(2.0))
        buf.clear()
        assert buf.pop() == ZERO

    def test_clear_on_tau_zero_resets(self):
        buf = LatencyBuffer(tau=0)
        buf.push(make_msg(5.0))
        buf.clear()
        # After clear, buffer is empty; for tau=0 we need 1 push to fill
        assert buf.pop() == ZERO

    def test_push_pop_works_normally_after_clear(self):
        buf = LatencyBuffer(tau=1)
        buf.push(make_msg(1.0))
        buf.push(make_msg(2.0))
        buf.clear()
        msg = make_msg(7.0)
        buf.push(msg)
        buf.push(make_msg(8.0))
        assert buf.pop() == msg

    def test_clear_on_empty_buffer_is_safe(self):
        buf = LatencyBuffer(tau=2)
        buf.clear()  # should not raise
        assert buf.pop() == ZERO


class TestMessageIntegrity:
    """Messages are returned unmodified."""

    def test_heterogeneous_message_unmodified(self):
        buf = LatencyBuffer(tau=0)
        msg = [float(i) * 0.1 for i in range(MSG_DIM)]
        buf.push(msg)
        assert buf.pop() == msg

    def test_negative_values_unmodified(self):
        buf = LatencyBuffer(tau=0)
        msg = [-float(i) for i in range(MSG_DIM)]
        buf.push(msg)
        assert buf.pop() == msg

    def test_custom_message_dim(self):
        buf = LatencyBuffer(tau=0, message_dim=8)
        zero = [0.0] * 8
        # Before push, zero vector has length 8
        buf2 = LatencyBuffer(tau=1, message_dim=8)
        assert buf2.pop() == zero
