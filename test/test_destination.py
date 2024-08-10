# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

from contextlib import nullcontext as does_not_raise
import pytest
import ax25.netrom


@pytest.mark.parametrize("call, mnem, neig, qual, expectation", [
    ('W1AW', 'DST1', 'KU6S', 42, does_not_raise()),
    ('W1AW-3', 'DST1', 'KU6S', 42, does_not_raise()),
    ('W1AW', 'DST1', 'KU6S-5', 42, does_not_raise()),
    ('W!AW', 'DST1', 'KU6S', 42, pytest.raises(ValueError)),
    (123.45, 'DST1', 'KU&S', 42, pytest.raises(TypeError)),
    ('W1AW', 'DST1', 'KU&S', 42, pytest.raises(ValueError)),
    ('W1AW', 'DST1234', 'KU6S', 42, pytest.raises(ValueError)),
    ('W1AW', 1234, 'KU6S', 42, pytest.raises(ValueError)),
    ('W1AW', 'DST1', 'KU6S', 442, pytest.raises(ValueError)),
    ('W1AW', 'DST1', 'KU6S', -42, pytest.raises(ValueError))
])
def test_construct(call, mnem, neig, qual, expectation):
    with expectation:
        d = ax25.netrom.Destination(call, mnem, neig, qual)
        assert str(d._callsign) == call
        assert d._mnemonic == mnem
        assert str(d._neighbor) == neig
        assert d._quality == qual


@pytest.mark.parametrize("in_call, in_neig, call, neig", [
    (ax25.Address('W1AW'), ax25.Address('KU6S'), 'W1AW', 'KU6S'),
    (ax25.Address('W1AW-3'), ax25.Address('KU6S'), 'W1AW-3', 'KU6S'),
    (ax25.Address('W1AW', 3), ax25.Address('KU6S'), 'W1AW-3', 'KU6S'),
    (ax25.Address('W1AW'), ax25.Address('KU6S-5'), 'W1AW', 'KU6S-5'),
    (ax25.Address('W1AW'), ax25.Address('KU6S', 5), 'W1AW', 'KU6S-5'),
    (ax25.Address('W1AW'), 'KU6S', 'W1AW', 'KU6S'),
    ('W1AW', ax25.Address('KU6S'), 'W1AW', 'KU6S')
])
def test_construct_addr(in_call, in_neig, call, neig):
    d = ax25.netrom.Destination(in_call, 'DST1', in_neig, 42)
    assert str(d._callsign) == call
    assert d._mnemonic == 'DST1'
    assert str(d._neighbor) == neig
    assert d._quality == 42


@pytest.mark.parametrize("in_call, in_mnem, in_neig, in_qual, s", [
    ('W1AW', 'DST1', 'KU6S', 42, 'W1AW (DST1) -> KU6S (42)'),
    ('W1AW-3', 'DST1', 'KU6S', 42, 'W1AW-3 (DST1) -> KU6S (42)'),
    ('W1AW', 'DST1', 'KU6S-5', 42, 'W1AW (DST1) -> KU6S-5 (42)'),
    ('W1AW', 'MYNODE', 'KU6S', 42, 'W1AW (MYNODE) -> KU6S (42)'),
    ('W1AW', 'MYNODE', 'KU6S', 0, 'W1AW (MYNODE) -> KU6S (0)'),
    ('W1AW', 'MYNODE', 'KU6S', 255, 'W1AW (MYNODE) -> KU6S (255)')
])
def test_str(in_call, in_mnem, in_neig, in_qual, s):
    d = ax25.netrom.Destination(in_call, in_mnem, in_neig, in_qual)
    assert str(d) == s


@pytest.mark.parametrize("in_call, in_mnem, in_neig, in_qual", [
    ('W1AW', 'DST1', 'KU6S', 42),
    ('W1AW-3', 'DST1', 'KU6S', 42),
    ('W1AW', 'DST1', 'KU6S-5', 42),
    ('W1AW', 'MYNODE', 'KU6S', 42),
    ('W1AW', 'MYNODE', 'KU6S', 0),
    ('W1AW', 'MYNODE', 'KU6S', 255)
])
def test_repr(in_call, in_mnem, in_neig, in_qual):
    d = ax25.netrom.Destination(in_call, in_mnem, in_neig, in_qual)
    rep = repr(d)
    assert rep.startswith('Destination(')
    assert rep.endswith(')')
    assert "callsign: {}".format(in_call) in rep
    assert "mnemonic: {}".format(in_mnem) in rep
    assert "neighbor: {}".format(in_neig) in rep
    assert "quality: {}".format(in_qual) in rep


@pytest.mark.parametrize("in_call, in_neig, call, ssid, ncall, nssid", [
    (ax25.Address('W1AW'), ax25.Address('KU6S'), 'W1AW', 0, 'KU6S', 0),
    (ax25.Address('W1AW-3'), ax25.Address('KU6S'), 'W1AW', 3, 'KU6S', 0),
    (ax25.Address('W1AW', 3), ax25.Address('KU6S'), 'W1AW', 3, 'KU6S', 0),
    (ax25.Address('W1AW'), ax25.Address('KU6S-5'), 'W1AW', 0, 'KU6S', 5),
    (ax25.Address('W1AW'), ax25.Address('KU6S', 5), 'W1AW', 0, 'KU6S', 5),
    (ax25.Address('W1AW'), 'KU6S', 'W1AW', 0, 'KU6S', 0),
    ('W1AW', ax25.Address('KU6S'), 'W1AW', 0, 'KU6S', 0)
])
def test_getter_callsign_neighbor(in_call, in_neig, call, ssid, ncall, nssid):
    d = ax25.netrom.Destination(in_call, 'DST1', in_neig, 42)
    assert d.callsign.call == call
    assert d.callsign.ssid == ssid
    assert d.best_neighbor.call == ncall
    assert d.best_neighbor.ssid == nssid


@pytest.mark.parametrize("in_mnem, in_qual, mnem, qual", [
    ('DST1', 0, 'DST1', 0),
    ('DST1', 42, 'DST1', 42),
    ('DST1', 255, 'DST1', 255)
])
def test_getter_mnemonic_quality(in_mnem, in_qual, mnem, qual):
    d = ax25.netrom.Destination('W1AW', in_mnem, 'KU6S', in_qual)
    assert d.mnemonic == mnem
    assert d.best_quality == qual


def test_pack():
    expected = (b'\xae\x62\x82\xae\x40\x40\x60\x44\x53\x54\x31'
                b'\x20\x20\x96\xaa\x6c\xa6\x40\x40\x60\x2a')
    d = ax25.netrom.Destination('W1AW', 'DST1', 'KU6S', 42)
    packed = d.pack()
    assert packed == expected


def test_unpack():
    packed = (b'\xae\x62\x82\xae\x40\x40\x00\x44\x53\x54\x31'
              b'\x20\x20\x96\xaa\x6c\xa6\x40\x40\x00\x2a')
    d = ax25.netrom.Destination.unpack(packed)
    assert str(d.callsign) == 'W1AW'
    assert d.mnemonic == 'DST1'
    assert str(d.best_neighbor) == 'KU6S'
    assert d.best_quality == 42
