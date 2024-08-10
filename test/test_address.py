# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

import pytest
import ax25


@pytest.mark.parametrize("in_call, in_base_only, result", [
    ('W1AW', False, True),
    ('W1AW-0', False, True),
    ('W1AW-1', False, True),
    ('W1AW-16', False, False),
    ('W1-AW-AW', False, False),
    ('W1!AW', False, False),
    ('W1AWAWAW', False, False),
    ('W1AW-32', False, False),
    ('W1AW-ABC', False, False),
    ('W1AW', True, True),
    ('W1AW-0', True, False),
    ('W1AW-1', True, False),
    ('W1AW-16', True, False),
    ('W1-AW-AW', True, False),
    ('W1!AW', True, False),
    ('W1AWAWAW', True, False),
    ('W1AW-32', True, False),
    ('W1AW-ABC', True, False)
])
def test_valid_call(in_call, in_base_only, result):
    assert ax25.Address.valid_call(in_call, in_base_only) == result


@pytest.mark.parametrize("in_call", [
    ('W1AW'),   # 1 x 2
    ('KU6S'),   # 2 x 1
    ('WW6HP'),  # 2 x 2
    ('K6EAG'),  # 1 x 3
    ('WR6ABD')  # 2 x 3
])
def test_callsign_patterns(in_call):
    addr = ax25.Address(in_call)
    assert addr._call == in_call
    assert addr._ssid == 0
    assert not addr._repeater
    assert not addr._command_response
    assert not addr._has_been_repeated


@pytest.mark.parametrize("in_call, call, ssid", [
    ('W1AW', 'W1AW', 0),
    ('W1AW-0', 'W1AW', 0),
    ('W1AW-1', 'W1AW', 1)
])
def test_callsign_only(in_call, call, ssid):
    addr = ax25.Address(in_call)
    assert addr._call == call
    assert addr._ssid == ssid
    assert not addr._repeater
    assert not addr._command_response
    assert not addr._has_been_repeated


@pytest.mark.parametrize("in_call, in_ssid, call, ssid", [
    ('W1AW', 1, 'W1AW', 1),
    ('W1AW-1', 1, 'W1AW', 1)
])
def test_callsign_and_ssid(in_call, in_ssid, call, ssid):
    addr = ax25.Address(in_call, in_ssid)
    assert addr._call == call
    assert addr._ssid == ssid
    assert not addr._repeater
    assert not addr._command_response
    assert not addr._has_been_repeated


@pytest.mark.parametrize("in_call, call, ssid, repeated", [
    ('W1AW', 'W1AW', 0, False),
    ('W1AW*', 'W1AW', 0, True),
    ('W1AW-2*', 'W1AW', 2, True)
])
def test_callsign_repeater(in_call, call, ssid, repeated):
    addr = ax25.Address(in_call, repeater=True)
    assert addr._call == call
    assert addr._ssid == ssid
    assert addr._repeater
    assert not addr._command_response
    assert addr._has_been_repeated == repeated


@pytest.mark.parametrize("in_call", [
    ('W1-AW-AW'),
    ('W1!AW'),
    ('W1AWAWAW'),
    ('W1AW-32'),
    ('W1AW-ABC')
])
def test_invalid_callsign(in_call):
    with pytest.raises(ValueError):
        _ = ax25.Address(in_call)


def test_ssid_conflict():
    with pytest.raises(ValueError):
        _ = ax25.Address("W1AW-2", 3)


def test_bad_repeater():
    with pytest.raises(TypeError):
        _ = ax25.Address("W1AW-1*")


@pytest.mark.parametrize("in_call, call", [
    ('W1AW', 'W1AW'),
    ('W1AW-0', 'W1AW'),
    ('W1AW-1', 'W1AW-1')
])
def test_str_callsign_only(in_call, call):
    assert str(ax25.Address(in_call)) == call


@pytest.mark.parametrize("in_call, in_ssid, call", [
    ('W1AW', 0, 'W1AW'),
    ('W1AW', 1, 'W1AW-1'),
    ('W1AW-1', 1, 'W1AW-1')
])
def test_str_callsign_and_ssid(in_call, in_ssid, call):
    assert str(ax25.Address(in_call, in_ssid)) == call


@pytest.mark.parametrize("in_call, call", [
    ('W1AW*', 'W1AW*'),
    ('W1AW-2*', 'W1AW-2*')
])
def test_str_callsign_only_repeated(in_call, call):
    assert str(ax25.Address(in_call, repeater=True)) == call


def test_str_callsign_and_ssid_repeated():
    assert str(ax25.Address("W1AW*", 2, True)) == "W1AW-2*"


@pytest.mark.parametrize(
    (
        "in_call, in_ssid, in_repeater, in_hbr, in_cr,"
        "rep_call, rep_ssid, rep_hbr, rep_cr"
    ),
    [
        ('W1AW', 0, False, None, None, 'W1AW', 0, None, False),
        ('W1AW', 1, False, None, None, 'W1AW', 1, None, False),
        ('W1AW-1', 0, False, None, None, 'W1AW', 1, None, False),
        ('W1AW', 2, False, None, True, 'W1AW', 2, None, True),
        ('W1AW', 0, True, None, None, 'W1AW', 0, False, None),
        ('W1AW', 1, True, None, None, 'W1AW', 1, False, None),
        ('W1AW*', 0, True, None, None, 'W1AW', 0, True, None),
        ('W1AW', 0, True, True, None, 'W1AW', 0, True, None)
    ])
def test_repr(
    in_call, in_ssid, in_repeater, in_hbr, in_cr,
        rep_call, rep_ssid, rep_hbr, rep_cr):
    addr = ax25.Address(in_call, in_ssid, in_repeater)
    if in_hbr is not None:
        addr.has_been_repeated = in_hbr
    if in_cr is not None:
        addr.command_response = in_cr
    rep = repr(addr)
    assert rep.startswith('Address(')
    assert rep.endswith(')')
    assert "call: {}".format(rep_call) in rep
    assert "ssid: {}".format(rep_ssid) in rep
    if in_repeater:
        assert "has_been_repeated: {}".format(rep_hbr) in rep
    else:
        assert "command_response: {}".format(rep_cr) in rep


def test_repeater_prop_unset():
    addr = ax25.Address("W1AW")
    assert not addr.repeater


@pytest.mark.parametrize("in_call, in_repeater, repeater", [
    ('W1AW', False, False),
    ('W1AW', True, True)
])
def test_repeater_prop_provided(in_call, in_repeater, repeater):
    addr = ax25.Address(in_call, repeater=in_repeater)
    assert addr.repeater == repeater


@pytest.mark.parametrize("in_call, has_been_repeated", [
    ('W1AW', False),
    ('W1AW*', True)
])
def test_repeated_prop(in_call, has_been_repeated):
    addr = ax25.Address(in_call, repeater=True)
    assert addr.has_been_repeated == has_been_repeated


def test_repeated_error():
    addr = ax25.Address("W1AW*", repeater=True)
    addr._repeater = False  # Field cannot be set via public access
    with pytest.raises(TypeError):
        _ = addr.has_been_repeated


@pytest.mark.parametrize("in_call, before, repeated, after", [
    ('W1AW', False, True, True),
    ('W1AW*', True, False, False)
])
def test_set_repeated(in_call, before, repeated, after):
    addr = ax25.Address(in_call, repeater=True)
    assert addr.has_been_repeated == before
    addr.has_been_repeated = repeated
    assert addr.has_been_repeated == after


def test_set_repeated_error():
    addr = ax25.Address("W1AW")
    with pytest.raises(TypeError):
        addr.has_been_repeated = True


def test_command_response_default():
    addr = ax25.Address("W1AW")
    assert not addr.command_response


def test_command_response_repeater():
    addr = ax25.Address("W1AW", repeater=True)
    with pytest.raises(TypeError):
        _ = addr.command_response


def test_set_command_response():
    addr = ax25.Address("W1AW")
    assert not addr.command_response
    addr.command_response = True
    assert addr.command_response


def test_set_command_response_repeater():
    addr = ax25.Address("W1AW", repeater=True)
    with pytest.raises(TypeError):
        addr.command_response = True


@pytest.mark.parametrize("in_call, packed_call", [
    ('WR6ABD', b'\xae\xa4\x6c\x82\x84\x88'),
    ('wr6abd', b'\xae\xa4\x6c\x82\x84\x88'),
    ('K6EAG', b'\x96\x6c\x8a\x82\x8e\x40'),
    ('KU6S', b'\x96\xaa\x6c\xa6\x40\x40')
])
def test_pack_callsign_only(in_call, packed_call):
    addr = ax25.Address(in_call)
    packed = addr.pack()
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == ax25.RESERVED


@pytest.mark.parametrize("in_call, packed_call", [
    ('WR6ABD', b'\xae\xa4\x6c\x82\x84\x88'),
    ('wr6abd', b'\xae\xa4\x6c\x82\x84\x88'),
    ('K6EAG', b'\x96\x6c\x8a\x82\x8e\x40'),
    ('KU6S', b'\x96\xaa\x6c\xa6\x40\x40')
])
def test_pack_callsign_only_bytes(in_call, packed_call):
    addr = ax25.Address(in_call)
    packed = bytes(addr)
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == ax25.RESERVED


@pytest.mark.parametrize("in_call, packed_call, last_byte", [
    ('W1AW-0', b'\xae\x62\x82\xae\x40\x40', 0x60),
    ('W1AW-1', b'\xae\x62\x82\xae\x40\x40', 0x62),
    ('W1AW-15', b'\xae\x62\x82\xae\x40\x40', 0x7E)
])
def test_pack_callsign_with_ssid(in_call, packed_call, last_byte):
    addr = ax25.Address(in_call)
    packed = addr.pack()
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == last_byte


@pytest.mark.parametrize("in_call, in_ssid, packed_call, last_byte", [
    ('W1AW', 0, b'\xae\x62\x82\xae\x40\x40', 0x60),
    ('W1AW', 1, b'\xae\x62\x82\xae\x40\x40', 0x62),
    ('W1AW', 15, b'\xae\x62\x82\xae\x40\x40', 0x7E)
])
def test_pack_callsign_and_ssid(in_call, in_ssid, packed_call, last_byte):
    addr = ax25.Address(in_call, in_ssid)
    packed = addr.pack()
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == last_byte


@pytest.mark.parametrize("in_call, packed_call, last_byte", [
    ('W1AW', b'\xae\x62\x82\xae\x40\x40', 0x60),
    ('W1AW*', b'\xae\x62\x82\xae\x40\x40', 0xE0),
    ('W1AW-3', b'\xae\x62\x82\xae\x40\x40', 0x66),
    ('W1AW-3*', b'\xae\x62\x82\xae\x40\x40', 0xE6)
])
def test_pack_has_been_repeated(in_call, packed_call, last_byte):
    addr = ax25.Address(in_call, repeater=True)
    packed = addr.pack()
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == last_byte


@pytest.mark.parametrize("in_call, in_cmdresp, packed_call, last_byte", [
    ('W1AW', False, b'\xae\x62\x82\xae\x40\x40', 0x60),
    ('W1AW', True, b'\xae\x62\x82\xae\x40\x40', 0xE0),
    ('W1AW-3', False, b'\xae\x62\x82\xae\x40\x40', 0x66),
    ('W1AW-3', True, b'\xae\x62\x82\xae\x40\x40', 0xE6)
])
def test_pack_command_response(in_call, in_cmdresp, packed_call, last_byte):
    addr = ax25.Address(in_call)
    addr.command_response = in_cmdresp
    packed = addr.pack()
    assert len(packed) == 7
    assert packed[0:6] == packed_call
    assert packed[6] == last_byte


@pytest.mark.parametrize("in_packed, call, ssid, cmdresp", [
    (b'\xae\x62\x82\xae\x40\x40\x60', 'W1AW', 0, False),
    (b'\xae\x62\x82\xae\x40\x40\x66', 'W1AW', 3, False),
    (b'\xae\x62\x82\xae\x40\x40\xE0', 'W1AW', 0, True),
    (b'\xae\x62\x82\xae\x40\x40\xE6', 'W1AW', 3, True),
    (b'\x96\x6c\x8a\x82\x8e\x40\x64', 'K6EAG', 2, False),
    (b'\xae\xa4\x6c\x82\x84\x88\x64', 'WR6ABD', 2, False)
])
def test_unpack_non_repeater(in_packed, call, ssid, cmdresp):
    addr = ax25.Address.unpack(in_packed)
    assert addr.call == call
    assert addr.ssid == ssid
    assert not addr.repeater
    assert addr.command_response == cmdresp


@pytest.mark.parametrize("in_packed, call, ssid, cmdresp", [
    (b'\xae\x62\x82\xae\x40\x40\x00', 'W1AW', 0, False),
    (b'\xae\x62\x82\xae\x40\x40\x06', 'W1AW', 3, False),
    (b'\xae\x62\x82\xae\x40\x40\x80', 'W1AW', 0, True),
    (b'\xae\x62\x82\xae\x40\x40\x86', 'W1AW', 3, True),
    (b'\x96\x6c\x8a\x82\x8e\x40\x04', 'K6EAG', 2, False),
    (b'\xae\xa4\x6c\x82\x84\x88\x04', 'WR6ABD', 2, False)
])
def test_unpack_non_repeater_ignore_reserved(in_packed, call, ssid, cmdresp):
    addr = ax25.Address.unpack(in_packed)
    assert addr.call == call
    assert addr.ssid == ssid
    assert not addr.repeater
    assert addr.command_response == cmdresp


def test_unpack_non_repeater_repeated():
    addr = ax25.Address.unpack(b'\x96\x88\x6c\xb2\x82\x9a\x00')
    with pytest.raises(TypeError):
        assert addr.has_been_repeated


@pytest.mark.parametrize("in_packed, call, ssid, repeated", [
    (b'\xae\x62\x82\xae\x40\x40\x60', 'W1AW', 0, False),
    (b'\xae\x62\x82\xae\x40\x40\x66', 'W1AW', 3, False),
    (b'\xae\x62\x82\xae\x40\x40\xE0', 'W1AW', 0, True),
    (b'\xae\x62\x82\xae\x40\x40\xE6', 'W1AW', 3, True),
    (b'\x96\x6c\x8a\x82\x8e\x40\x64', 'K6EAG', 2, False),
    (b'\xae\xa4\x6c\x82\x84\x88\x64', 'WR6ABD', 2, False)
])
def test_unpack_repeater(in_packed, call, ssid, repeated):
    addr = ax25.Address.unpack(in_packed, repeater=True)
    assert addr.call == call
    assert addr.ssid == ssid
    assert addr.repeater
    assert addr.has_been_repeated == repeated


@pytest.mark.parametrize("in_packed, call, ssid, repeated", [
    (b'\xae\x62\x82\xae\x40\x40\x00', 'W1AW', 0, False),
    (b'\xae\x62\x82\xae\x40\x40\x06', 'W1AW', 3, False),
    (b'\xae\x62\x82\xae\x40\x40\x80', 'W1AW', 0, True),
    (b'\xae\x62\x82\xae\x40\x40\x86', 'W1AW', 3, True),
    (b'\x96\x6c\x8a\x82\x8e\x40\x04', 'K6EAG', 2, False),
    (b'\xae\xa4\x6c\x82\x84\x88\x04', 'WR6ABD', 2, False)
])
def test_unpack_repeater_ignore_reserved(in_packed, call, ssid, repeated):
    addr = ax25.Address.unpack(in_packed, repeater=True)
    assert addr.call == call
    assert addr.ssid == ssid
    assert addr.repeater
    assert addr.has_been_repeated == repeated


def test_unpack_repeater_cmdresp():
    addr = ax25.Address.unpack(b'\xae\x62\x82\xae\x40\x40\x00', True)
    with pytest.raises(TypeError):
        assert addr.command_response


def test_unpack_invalid_callsign():
    with pytest.raises(ValueError):
        _ = ax25.Address.unpack(b'\xae\x42\x82\xae\x40\x40\x00')
