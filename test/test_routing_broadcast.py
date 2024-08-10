# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

from contextlib import nullcontext as does_not_raise
import pytest
import ax25.netrom


@pytest.mark.parametrize("sender, destinations, expectation", [
    ('MYNODE', None, does_not_raise()),
    ('', None, pytest.raises(ValueError)),
    (42, None, pytest.raises(ValueError)),
    ('MYNODEX', None, pytest.raises(ValueError)),
    ('MYNODE', [], does_not_raise()),
    ('MYNODE', 42, pytest.raises(TypeError)),
    ('MYNODE', [42], pytest.raises(TypeError)),
    ('MYNODE', [ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42)],
        does_not_raise()),
    ('MYNODE',
        [
            ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42),
            ax25.netrom.Destination('WR6ABD', 'NODE1', 'K6EAG', 21)
        ],
        does_not_raise())
])
def test_construct(sender, destinations, expectation):
    with expectation:
        rb = ax25.netrom.RoutingBroadcast(sender, destinations)
        assert rb._sender == sender
        if destinations:
            assert len(rb._destinations) == len(destinations)
            for d in destinations:
                assert d in rb._destinations
        else:
            assert rb._destinations is None


def test_repr_no_dest():
    rb = ax25.netrom.RoutingBroadcast('MYNODE', None)
    rep = repr(rb)
    assert rep.startswith('RoutingBroadcast(')
    assert rep.endswith(')')
    assert "sender: MYNODE" in rep
    assert "destinations:" not in rep


@pytest.mark.parametrize("destinations", [
    ([ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42)]),
    ([
        ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42),
        ax25.netrom.Destination('WR6ABD', 'NODE1', 'K6EAG', 21)
    ])
])
def test_repr(destinations):
    rb = ax25.netrom.RoutingBroadcast('MYNODE', destinations)
    rep = repr(rb)
    assert rep.startswith('RoutingBroadcast(')
    assert rep.endswith(')')
    assert "sender: MYNODE" in rep
    assert "destinations:" in rep
    for d in destinations:
        assert repr(d) in rep


@pytest.mark.parametrize("sender, destinations", [
    ('MYNODE', None),
    ('MYNODE', [ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42)]),
    ('MYNODE',
        [
            ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42),
            ax25.netrom.Destination('WR6ABD', 'NODE1', 'K6EAG', 21)
        ])
])
def test_getters(sender, destinations):
    rb = ax25.netrom.RoutingBroadcast(sender, destinations)
    assert rb.sender == sender
    if destinations:
        assert len(rb.destinations) == len(destinations)
        for d in destinations:
            assert d in rb.destinations
    else:
        assert rb.destinations is None


@pytest.mark.parametrize("sender, destinations, expected", [
    ('MYNODE', None,
        b'\xffMYNODE'),
    ('MYNODE', [ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42)],
        b'\xffMYNODE'
        b'\xae\x62\x82\xae\x40\x40\x60NODE1 '
        b'\x96\xaa\x6c\xa6\x40\x40\x60\x2a'),
    ('MYNODE',
        [
            ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42),
            ax25.netrom.Destination('WR6ABD', 'NODE2', 'K6EAG', 21)
        ],
        b'\xffMYNODE'
        b'\xae\x62\x82\xae\x40\x40\x60NODE1 '
        b'\x96\xaa\x6c\xa6\x40\x40\x60\x2a'
        b'\xae\xa4\x6c\x82\x84\x88\x60NODE2 '
        b'\x96\x6c\x8a\x82\x8e\x40\x60\x15')
])
def test_pack(sender, destinations, expected):
    rb = ax25.netrom.RoutingBroadcast(sender, destinations)
    packed = rb.pack()
    assert packed == expected


@pytest.mark.parametrize(
    "in_packed, sender, destinations",
    [
        (
            b'\xffMYNODE',
            'MYNODE', None
        ),
        (
            b'\xffMYNODE'
            b'\xae\x62\x82\xae\x40\x40\x00NODE1 '
            b'\x96\xaa\x6c\xa6\x40\x40\x00\x2a',
            'MYNODE', [ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42)]
        ),
        (
            b'\xffMYNODE'
            b'\xae\x62\x82\xae\x40\x40\x00NODE1 '
            b'\x96\xaa\x6c\xa6\x40\x40\x00\x2a'
            b'\xae\xa4\x6c\x82\x84\x88\x00NODE2 '
            b'\x96\x6c\x8a\x82\x8e\x40\x00\x15',
            'MYNODE',
            [
                ax25.netrom.Destination('W1AW', 'NODE1', 'KU6S', 42),
                ax25.netrom.Destination('WR6ABD', 'NODE2', 'K6EAG', 21)
            ]
        )
    ])
def test_unpack(in_packed, sender, destinations):
    rb = ax25.netrom.RoutingBroadcast.unpack(in_packed)
    assert rb.sender == sender
    if destinations:
        assert len(rb.destinations) == len(destinations)
        dest_str = [str(d) for d in destinations]
        for d in rb.destinations:
            assert str(d) in dest_str
    else:
        assert rb.destinations is None


def test_unpack_bad():
    packed = b'\xeeMYNODE'
    with pytest.raises(TypeError):
        _ = ax25.netrom.RoutingBroadcast.unpack(packed)
