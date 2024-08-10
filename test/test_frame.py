# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

from contextlib import nullcontext as does_not_raise
import pytest
import ax25


@pytest.mark.parametrize(
    "in_dst, in_src, dst_call, dst_ssid, src_call, src_ssid",
    [
        ('WR6ABD-5', 'W1AW', 'WR6ABD', 5, 'W1AW', 0),
        ('WR6ABD-0', 'W1AW-3', 'WR6ABD', 0, 'W1AW', 3),
        (ax25.Address('WR6ABD-5'), ax25.Address('W1AW'),
            'WR6ABD', 5, 'W1AW', 0),
        (ax25.Address('WR6ABD-0'), ax25.Address('W1AW-3'),
            'WR6ABD', 0, 'W1AW', 3),
        (ax25.Address('WR6ABD-5'), 'W1AW', 'WR6ABD', 5, 'W1AW', 0),
        ('WR6ABD-5', ax25.Address('W1AW'), 'WR6ABD', 5, 'W1AW', 0)
    ])
def test_construct_addresses(
        in_dst, in_src, dst_call, dst_ssid, src_call, src_ssid):
    ctl = ax25.Control(ax25.FrameType.UI)
    f = ax25.Frame(in_dst, in_src, control=ctl)
    assert isinstance(f.dst, ax25.Address)
    assert f.dst.call == dst_call
    assert f.dst.ssid == dst_ssid
    assert isinstance(f.src, ax25.Address)
    assert f.src.call == src_call
    assert f.src.ssid == src_ssid


@pytest.mark.parametrize("in_dst, in_src, expectation", [
    ('W1AW', 'WR6ABD', does_not_raise()),
    (42, 'WR6ABD', pytest.raises(TypeError)),
    ('W1AW', False, pytest.raises(TypeError))
])
def test_construct_addresses_error(in_dst, in_src, expectation):
    ctl = ax25.Control(ax25.FrameType.UI)
    with expectation:
        _ = ax25.Frame(in_dst, in_src, control=ctl)


@pytest.mark.parametrize("in_via, expectation", [
    (['W1AW'], does_not_raise()),
    ([ax25.Address('W1AW')], does_not_raise()),
    (['W1AW', 'WR6ABD'], does_not_raise()),
    (('W1AW', 'WR6ABD'), does_not_raise()),
    (42, pytest.raises(TypeError)),
    ([42], pytest.raises(TypeError))
])
def test_construct_via(in_via, expectation):
    ctl = ax25.Control(ax25.FrameType.UI)
    with expectation:
        _ = ax25.Frame('W1AW', 'WR6ABD', control=ctl, via=in_via)


@pytest.mark.parametrize("in_ctl, expectation", [
    (ax25.Control(ax25.FrameType.UI), does_not_raise()),
    (0x13, does_not_raise()),
    ("bad", pytest.raises(TypeError))
])
def test_construct_control(in_ctl, expectation):
    with expectation:
        _ = ax25.Frame('W1AW', 'WR6ABD', control=in_ctl)


@pytest.mark.parametrize("in_ft, in_pid, pid", [
    (ax25.FrameType.I,  0xF0, 0xF0),
    (ax25.FrameType.RR, 0xF0, 0x00),
    (ax25.FrameType.UI, 0xF0, 0xF0)
])
def test_construct_pid(in_ft, in_pid, pid):
    ctl = ax25.Control(in_ft)
    f = ax25.Frame('W1AW', 'WR6ABD', control=ctl, pid=in_pid)
    assert f._pid == pid


@pytest.mark.parametrize("in_ft, in_data, expectation", [
    (ax25.FrameType.I,  None, does_not_raise()),
    (ax25.FrameType.I,  b'abc', does_not_raise()),
    (ax25.FrameType.I,  bytearray(b'abc'), does_not_raise()),
    (ax25.FrameType.I,  bytearray(b'a' * 300), pytest.raises(ValueError)),
    (ax25.FrameType.I,  42, pytest.raises(TypeError)),
    (ax25.FrameType.RR, None, does_not_raise()),
    (ax25.FrameType.RR, b'abc', pytest.raises(ValueError)),
    (ax25.FrameType.UI,  None, does_not_raise()),
    (ax25.FrameType.UI,  b'abc', does_not_raise()),
    (ax25.FrameType.UI,  bytearray(b'a' * 300), pytest.raises(ValueError)),
    (ax25.FrameType.UI,  42, pytest.raises(TypeError))
])
def test_construct_data(in_ft, in_data, expectation):
    ctl = ax25.Control(in_ft)
    with expectation:
        _ = ax25.Frame('W1AW', 'WR6ABD', control=ctl, data=in_data)


def test_getter_dst():
    ctl = ax25.Control(ax25.FrameType.UI)
    f = ax25.Frame('W1AW-3', 'WR6ABD', control=ctl)
    dst = f.dst
    assert isinstance(dst, ax25.Address)
    assert dst.call == 'W1AW'
    assert dst.ssid == 3


def test_getter_src():
    ctl = ax25.Control(ax25.FrameType.UI)
    f = ax25.Frame('W1AW', 'WR6ABD-3', control=ctl)
    src = f.src
    assert isinstance(src, ax25.Address)
    assert src.call == 'WR6ABD'
    assert src.ssid == 3


def test_getter_via():
    in_via = ['W1AW', 'WR6ABD']
    ctl = ax25.Control(ax25.FrameType.UI)
    f = ax25.Frame('W1AW', 'WR6ABD', in_via, ctl)
    via = f.via
    assert isinstance(via, tuple)
    assert len(via) == len(in_via)
    assert str(via[0]) == in_via[0]
    assert str(via[1]) == in_via[1]


def test_getter_control():
    ctl = ax25.Control(ax25.FrameType.UI, poll_final=True)
    f = ax25.Frame('W1AW', 'WR6ABD', control=ctl)
    ctl2 = f.control
    assert ctl2.frame_type == ctl.frame_type
    assert ctl2.poll_final == ctl.poll_final


@pytest.mark.parametrize("in_ft, in_pid, pid", [
    (ax25.FrameType.I,  0xF0, 0xF0),
    (ax25.FrameType.RR, 0xF0, 0x00),
    (ax25.FrameType.UI, 0xF0, 0xF0)
])
def test_getter_pid(in_ft, in_pid, pid):
    ctl = ax25.Control(in_ft)
    f = ax25.Frame('W1AW', 'WR6ABD', control=ctl, pid=in_pid)
    assert f.pid == pid


@pytest.mark.parametrize("in_ft, in_data, data", [
    (ax25.FrameType.I,  None, None),
    (ax25.FrameType.I,  b'abc', b'abc'),
    (ax25.FrameType.I,  bytearray(b'abc'), b'abc'),
    (ax25.FrameType.RR, None, None),
    (ax25.FrameType.UI,  None, None),
    (ax25.FrameType.UI,  b'abc', b'abc'),
    (ax25.FrameType.UI,  bytearray(b'abc'), b'abc')
])
def test_getter_data(in_ft, in_data, data):
    ctl = ax25.Control(in_ft)
    f = ax25.Frame('W1AW', 'WR6ABD', control=ctl, data=in_data)
    assert f.data == data


@pytest.mark.parametrize(
    "in_ft, in_dst, in_src, in_via, in_pid, in_data, expected",
    [
        (ax25.FrameType.RR, 'W1AW', 'WR6ABD', None, 0x00, None,
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x01'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', None, 0xF0,
            b'Hello',
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x03\xf0Hello'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', None, 0xF0,
            bytearray(b'Hello'),
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x03\xf0Hello'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', ['K6EAG', 'KU6S'], 0xF0,
            b'Hello',
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x60'
            b'\x96\x6c\x8a\x82\x8e\x40\x60'
            b'\x96\xaa\x6c\xa6\x40\x40\x61'
            b'\x03\xf0Hello')
    ])
def test_pack(in_ft, in_dst, in_src, in_via, in_pid, in_data, expected):
    ctl = ax25.Control(in_ft)
    f = ax25.Frame(
        in_dst, in_src, control=ctl, via=in_via, pid=in_pid, data=in_data)
    packed = f.pack()
    assert packed == expected


@pytest.mark.parametrize(
    "in_ft, in_dst, in_src, in_via, in_pid, in_data, expected",
    [
        (ax25.FrameType.RR, 'W1AW', 'WR6ABD', None, 0x00, None,
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x01'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', None, 0xF0,
            b'Hello',
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x03\xf0Hello'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', None, 0xF0,
            bytearray(b'Hello'),
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x61'
            b'\x03\xf0Hello'),
        (ax25.FrameType.UI, 'W1AW', 'WR6ABD', ['K6EAG', 'KU6S'], 0xF0,
            b'Hello',
            b'\xae\x62\x82\xae\x40\x40\x60'
            b'\xae\xa4\x6c\x82\x84\x88\x60'
            b'\x96\x6c\x8a\x82\x8e\x40\x60'
            b'\x96\xaa\x6c\xa6\x40\x40\x61'
            b'\x03\xf0Hello')
    ])
def test_pack_bytes(in_ft, in_dst, in_src, in_via, in_pid, in_data, expected):
    ctl = ax25.Control(in_ft)
    f = ax25.Frame(
        in_dst, in_src, control=ctl, via=in_via, pid=in_pid, data=in_data)
    packed = bytes(f)
    assert packed == expected


@pytest.mark.parametrize(
    "in_packed, ft, dst, src, via, pid, data",
    [
        (
            b'\xae\x62\x82\xae\x40\x40\x00'
            b'\xae\xa4\x6c\x82\x84\x88\x01'
            b'\x01',
            ax25.FrameType.RR, 'W1AW', 'WR6ABD', None, 0x00, None
        ),
        (
            b'\xae\x62\x82\xae\x40\x40\x00'
            b'\xae\xa4\x6c\x82\x84\x88\x01'
            b'\x03\xf0Hello',
            ax25.FrameType.UI, 'W1AW', 'WR6ABD', None, 0xF0,
            b'Hello'),
        (
            b'\xae\x62\x82\xae\x40\x40\x00'
            b'\xae\xa4\x6c\x82\x84\x88\x00'
            b'\x96\x6c\x8a\x82\x8e\x40\x00'
            b'\x96\xaa\x6c\xa6\x40\x40\x01'
            b'\x03\xf0Hello',
            ax25.FrameType.UI, 'W1AW', 'WR6ABD', ['K6EAG', 'KU6S'], 0xF0,
            b'Hello'
        )
    ])
def test_unpack(in_packed, ft, dst, src, via, pid, data):
    f = ax25.Frame.unpack(in_packed)
    assert f.control.frame_type == ft
    assert str(f.dst) == dst
    assert str(f.src) == src
    if via:
        assert f.via is not None
        assert len(f.via) == len(via)
        for i, v in enumerate(f.via):
            assert str(v) == via[i]
    else:
        assert f.via is None
    assert f.pid == pid
    assert f.data == data
