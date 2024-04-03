# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

import pytest
import ax25


@pytest.mark.parametrize("in_type, is_i", [
    (ax25.FrameType.RR,    False),
    (ax25.FrameType.RNR,   False),
    (ax25.FrameType.REJ,   False),
    (ax25.FrameType.SREJ,  False),
    (ax25.FrameType.UI,    False),
    (ax25.FrameType.DM,    False),
    (ax25.FrameType.SABM,  False),
    (ax25.FrameType.DISC,  False),
    (ax25.FrameType.UA,    False),
    (ax25.FrameType.SABME, False),
    (ax25.FrameType.FRMR,  False),
    (ax25.FrameType.XID,   False),
    (ax25.FrameType.TEST,  False),
    (ax25.FrameType.I,     True),
    (ax25.FrameType.S,     False),
    (ax25.FrameType.U,     False)
])
def test_frame_type_i(in_type, is_i):
    assert in_type.is_I() == is_i


@pytest.mark.parametrize("in_type, is_s", [
    (ax25.FrameType.RR,    True),
    (ax25.FrameType.RNR,   True),
    (ax25.FrameType.REJ,   True),
    (ax25.FrameType.SREJ,  True),
    (ax25.FrameType.UI,    False),
    (ax25.FrameType.DM,    False),
    (ax25.FrameType.SABM,  False),
    (ax25.FrameType.DISC,  False),
    (ax25.FrameType.UA,    False),
    (ax25.FrameType.SABME, False),
    (ax25.FrameType.FRMR,  False),
    (ax25.FrameType.XID,   False),
    (ax25.FrameType.TEST,  False),
    (ax25.FrameType.I,     False),
    (ax25.FrameType.S,     True),
    (ax25.FrameType.U,     False)
])
def test_frame_type_s(in_type, is_s):
    assert in_type.is_S() == is_s


@pytest.mark.parametrize("in_type, is_u", [
    (ax25.FrameType.RR,    False),
    (ax25.FrameType.RNR,   False),
    (ax25.FrameType.REJ,   False),
    (ax25.FrameType.SREJ,  False),
    (ax25.FrameType.UI,    True),
    (ax25.FrameType.DM,    True),
    (ax25.FrameType.SABM,  True),
    (ax25.FrameType.DISC,  True),
    (ax25.FrameType.UA,    True),
    (ax25.FrameType.SABME, True),
    (ax25.FrameType.FRMR,  True),
    (ax25.FrameType.XID,   True),
    (ax25.FrameType.TEST,  True),
    (ax25.FrameType.I,     False),
    (ax25.FrameType.S,     False),
    (ax25.FrameType.U,     True)
])
def test_frame_type_u(in_type, is_u):
    assert in_type.is_U() == is_u
