# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

from contextlib import nullcontext as does_not_raise
import pytest
import ax25


pack_test_data = {
    (ax25.FrameType.I, False, 0, 0): 0x00,
    (ax25.FrameType.I, True, 0, 0): 0x10,
    (ax25.FrameType.I, False, 3, 0): 0x60,
    (ax25.FrameType.I, False, 0, 7): 0x0E,
    (ax25.FrameType.I, False, 3, 7): 0x6E,
    (ax25.FrameType.I, True, 3, 7): 0x7E,
    (ax25.FrameType.RR, False, 0, 0): 0x01,
    (ax25.FrameType.RR, True, 0, 0): 0x11,
    (ax25.FrameType.RR, False, 3, 0): 0x61,
    (ax25.FrameType.RR, False, 0, 7): 0x01,
    (ax25.FrameType.RR, False, 3, 7): 0x61,
    (ax25.FrameType.RR, True, 3, 7): 0x71,
    (ax25.FrameType.UI, False, 0, 0): 0x03,
    (ax25.FrameType.UI, True, 0, 0): 0x13,
    (ax25.FrameType.UI, False, 3, 0): 0x03,
    (ax25.FrameType.UI, False, 0, 7): 0x03,
    (ax25.FrameType.UI, False, 3, 7): 0x03,
    (ax25.FrameType.UI, True, 3, 7): 0x13
}


unpack_test_data = {
    0x00: (ax25.FrameType.I, False, 0, 0),
    0x10: (ax25.FrameType.I, True, 0, 0),
    0x60: (ax25.FrameType.I, False, 3, 0),
    0x0E: (ax25.FrameType.I, False, 0, 7),
    0x6E: (ax25.FrameType.I, False, 3, 7),
    0x7E: (ax25.FrameType.I, True, 3, 7),
    0x01: (ax25.FrameType.RR, False, 0, 0),
    0x11: (ax25.FrameType.RR, True, 0, 0),
    0x61: (ax25.FrameType.RR, False, 3, 0),
    0x71: (ax25.FrameType.RR, True, 3, 0),
    0x03: (ax25.FrameType.UI, False, 0, 0),
    0x13: (ax25.FrameType.UI, True, 0, 0)
}


@pytest.mark.parametrize("in_ft, ft", [
    (ft, ft) for ft in ax25.FrameType])
def test_construct_internal_defaults(in_ft, ft):
    ctl = ax25.Control(in_ft)
    assert ctl._frame_type == ft
    assert not ctl._poll_final
    assert ctl._recv_seqno == 0
    assert ctl._send_seqno == 0


@pytest.mark.parametrize("ft", [ax25.FrameType.RR, ax25.FrameType.I])
@pytest.mark.parametrize("pf", [True, False])
@pytest.mark.parametrize("nr", [0, 1, 2])
@pytest.mark.parametrize("ns", [0, 1, 2])
def test_construct_internal_args(ft, pf, nr, ns):
    ctl = ax25.Control(ft, poll_final=pf, recv_seqno=nr, send_seqno=ns)
    assert ctl._frame_type == ft
    assert ctl._poll_final == pf
    assert ctl._recv_seqno == nr
    assert ctl._send_seqno == ns


@pytest.fixture
def expected_str(request):
    key = (
        request.node.funcargs['ft'],
        request.node.funcargs['pf'],
        request.node.funcargs['nr'],
        request.node.funcargs['ns']
    )
    return '{:02X}'.format(pack_test_data[key])


@pytest.mark.parametrize("ft, pf, nr, ns", pack_test_data.keys())
def test_str(ft, pf, nr, ns, expected_str):
    ctl = ax25.Control(ft, poll_final=pf, recv_seqno=nr, send_seqno=ns)
    assert str(ctl) == expected_str


@pytest.mark.parametrize("ft, pf, nr, ns", pack_test_data.keys())
def test_repr(ft, pf, nr, ns):
    ctl = ax25.Control(ft, poll_final=pf, recv_seqno=nr, send_seqno=ns)
    rep = repr(ctl)
    assert rep.startswith('Control(')
    assert rep.endswith(')')
    assert "type: {}".format(ft.name) in rep
    assert "poll_final: {}".format(pf) in rep
    if ft.is_I() or ft.is_S():
        assert "recv_seqno: {}".format(nr) in rep
    if ft.is_I():
        assert "send_seqno: {}".format(ns) in rep


@pytest.mark.parametrize("in_ft, ft", [
    (ft, ft) for ft in ax25.FrameType])
def test_getter_ft(in_ft, ft):
    ctl = ax25.Control(in_ft)
    assert ctl.frame_type == ft


@pytest.mark.parametrize("ft", [ax25.FrameType.RR, ax25.FrameType.I])
@pytest.mark.parametrize("pf", [True, False])
def test_getter_poll_final(ft, pf):
    ctl = ax25.Control(ft, poll_final=pf)
    assert ctl.poll_final == pf


@pytest.mark.parametrize("in_ft, value, expectation", [
    (ax25.FrameType.I,  0, does_not_raise()),         # I frame ok
    (ax25.FrameType.RR, 0, does_not_raise()),         # S frame ok
    (ax25.FrameType.UI, 0, pytest.raises(TypeError))  # U frame not valid
])
def test_getter_nr(in_ft, value, expectation):
    ctl = ax25.Control(in_ft)
    with expectation:
        assert ctl.recv_seqno == value


@pytest.mark.parametrize("in_ft, value, expectation", [
    (ax25.FrameType.I,  0, does_not_raise()),          # I frame ok
    (ax25.FrameType.RR, 0, pytest.raises(TypeError)),  # S frame not valid
    (ax25.FrameType.UI, 0, pytest.raises(TypeError))   # U frame not valid
])
def test_getter_ns(in_ft, value, expectation):
    ctl = ax25.Control(in_ft)
    with expectation:
        assert ctl.send_seqno == value


@pytest.mark.parametrize("ft", [ax25.FrameType.RR, ax25.FrameType.I])
@pytest.mark.parametrize("pf", [True, False])
def test_setter_poll_final(ft, pf):
    ctl = ax25.Control(ft)
    ctl.poll_final = pf
    assert ctl.poll_final == pf


@pytest.mark.parametrize("in_ft, value, expectation", [
    (ax25.FrameType.I,  1, does_not_raise()),         # I frame ok
    (ax25.FrameType.RR, 1, does_not_raise()),         # S frame ok
    (ax25.FrameType.UI, 1, pytest.raises(TypeError))  # U frame not valid
])
def test_setter_nr(in_ft, value, expectation):
    ctl = ax25.Control(in_ft)
    with expectation:
        ctl.recv_seqno = value


@pytest.mark.parametrize("in_ft, value, expectation", [
    (ax25.FrameType.I,  1, does_not_raise()),          # I frame ok
    (ax25.FrameType.RR, 1, pytest.raises(TypeError)),  # S frame not valid
    (ax25.FrameType.UI, 1, pytest.raises(TypeError))   # U frame not valid
])
def test_setter_ns(in_ft, value, expectation):
    ctl = ax25.Control(in_ft)
    with expectation:
        ctl.send_seqno = value


@pytest.fixture
def expected_pack(request):
    key = (
        request.node.funcargs['ft'],
        request.node.funcargs['pf'],
        request.node.funcargs['nr'],
        request.node.funcargs['ns']
    )
    return pack_test_data[key]


@pytest.mark.parametrize("ft, pf, nr, ns", pack_test_data.keys())
def test_pack(ft, pf, nr, ns, expected_pack):
    ctl = ax25.Control(ft, poll_final=pf, recv_seqno=nr, send_seqno=ns)
    packed = ctl.pack()
    assert packed == expected_pack


@pytest.mark.parametrize("ft, pf, nr, ns", pack_test_data.keys())
def test_pack_int(ft, pf, nr, ns, expected_pack):
    ctl = ax25.Control(ft, poll_final=pf, recv_seqno=nr, send_seqno=ns)
    packed = int(ctl)
    assert packed == expected_pack


def test_pack_err():
    ctl = ax25.Control(ax25.FrameType.UNK)
    with pytest.raises(ValueError):
        _ = ctl.pack()


@pytest.fixture
def expected_unpack(request):
    key = request.node.funcargs['packed']
    return unpack_test_data[key]


@pytest.mark.parametrize("packed", unpack_test_data.keys())
def test_unpack(packed, expected_unpack):
    ctl = ax25.Control.unpack(packed)
    assert ctl.frame_type == expected_unpack[0]
    assert ctl.poll_final == expected_unpack[1]
    # Check nr and ns against internals to avoid access exceptions
    assert ctl._recv_seqno == expected_unpack[2]
    assert ctl._send_seqno == expected_unpack[3]
