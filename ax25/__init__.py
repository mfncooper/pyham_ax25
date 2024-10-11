# =============================================================================
# Copyright (c) 2018-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
AX.25 Frame Structure

Structure definitions together with methods to pack and unpack native AX.25
frames and the constituent parts of those frames. This can be used together
with a communication protocol such as AGWPE, KISS, or a native AX.25 stack
for applications across the gamut, from simple 'listen' monitoring to full
connected mode systems.

Protocol reference:
  http://www.tapr.org/pdf/AX25.2.2.pdf
"""

__author__ = 'Martin F N Cooper'
__version__ = '1.0.2'

from enum import Enum

# Addressing
ALEN = 6             # Basic address length (callsign only)
AXLEN = 7            # Extended address length (with SSID)
OFF_DST = 0          # Offset to destination address
OFF_SRC = AXLEN      # Offset to source address
OFF_VIA = AXLEN * 2  # Offset to 'via' fields

# SSID byte
HDLC_AEB    = 0x01  # HDLC address extension bit
SSID        = 0x1E  # SSID mask
CMDRESP     = 0x80  # Command / response
REPEATED    = 0x80  # Has been repeated
RESERVED    = 0x60  # Reserved bits
SSSID_SPARE = 0x40  # EAX25
ESSID_SPARE = 0x20  # DAMA

# Frame control byte
PF  = 0x10  # P/F
NR  = 0xE0  # N(R) mask
NRS = 5     # N(R) shift
NS  = 0x0E  # N(S) mask
NSS = 1     # N(S) shift


class FrameType(Enum):
    """
    The type of an AX.25 frame, as identified within the control field.

    The values match those defined in the AX.25 spec, with an additional value
    to identify an as yet unknown frame. General types are also defined, to
    allow for categorization of I, S and U frames, along with methods to
    determine whether a value matches a specific category.
    """
    # S frame types
    RR    = 0x01
    """ Receive Ready """
    RNR   = 0x05
    """ Receive Not Ready """
    REJ   = 0x09
    """ Reject """
    SREJ  = 0x0D
    """ Selective Reject """
    # U frame types
    UI    = 0x03
    """ Unnumbered Information """
    DM    = 0x0F
    """ Disconnect Mode """
    SABM  = 0x2F
    """ Set Async Balanced Mode """
    DISC  = 0x43
    """ Disconnect """
    UA    = 0x63
    """ Unnumbered Acknowledge """
    SABME = 0x6F
    """ Set Async Balanced Mode """
    FRMR  = 0x87
    """ Frame Reject """
    XID   = 0xAF
    """ Exchange Identification """
    TEST  = 0xE3
    """ Test """
    # Unknown frame type
    UNK   = 0xFF
    """ Unknown frame type """
    # General frame types
    I     = 0x00  # noqa: E741
    """ I Frame """
    S     = 0x01
    """ S Frame """
    U     = 0x03
    """ U Frame """

    def is_I(self):  # noqa N802
        """ Is this an I frame type? """
        return self.value & 0x01 == 0x00

    def is_S(self):  # noqa N802
        """ Is this an S frame type? """
        return self.value & 0x03 == 0x01

    def is_U(self):  # noqa N802
        """ Is this an U frame type? """
        return self.value & 0x03 == 0x03


class Address:
    """
    A single element (subfield) of the address field for an AX.25 frame.

    In addition to the callsign and SSID, this includes fields corresponding
    to has-been-repeated and command/response state.

    :param str call: Callsign, with or without an SSID. If an SSID is included
        in this string, the `ssid` argument must not be used. If the callsign
        ends with an asterisk, the address is marked as having been repeated.
    :param int ssid: SSID, in the range 0..15.
    :param bool repeater: Indicates whether or not this instance represents a
        repeater address. This is used to determine whether this instance has
        a command/response bit or a has-been-repeated bit.
    :raises TypeError: if the `repeater` argument is `False` but the callsign
        ends with an asterisk.
    :raises ValueError: if the callsign or SSID is invalid, or if the callsign
        includes an SSID value that conflicts with the `ssid` argument.
    """
    def __init__(self, call, ssid=0, repeater=False):
        self._repeater = repeater
        self._command_response = False
        self._has_been_repeated = False
        if call.endswith('*'):
            if repeater:
                self._has_been_repeated = True
                call = call[:-1]
            else:
                raise TypeError(
                    'Cannot set has_been_repeated on non-repeater address')
        parts = call.split('-')
        if len(parts) > 2 or not self.valid_call(parts[0], True):
            raise ValueError('Invalid callsign')
        if len(parts) == 2:
            ssid2 = int(parts[1])
            if ssid != 0 and ssid2 != ssid:
                raise ValueError('SSID conflict')
            ssid = ssid2
        if ssid > 15:
            raise ValueError('Invalid SSID')
        self._call = parts[0].upper()
        self._ssid = ssid

    def __repr__(self):
        return ('Address(call: {}, ssid: {}, repeater: {}, {}: {})').format(
            self._call, self._ssid, self._repeater,
            ('has_been_repeated' if self._repeater
                else 'command_response'),
            (self._has_been_repeated if self._repeater
                else self._command_response))

    def __str__(self):
        call = self._call
        if self._ssid:
            call += '-' + str(self._ssid)
        if self._repeater and self._has_been_repeated:
            call += '*'
        return call

    def __bytes__(self):
        return self.pack()

    @staticmethod
    def valid_call(call, base_only=False):
        """
        Check a callsign to determine its validity.

        The following checks are performed:

         - Base callsign is of a valid length, and is alphanumeric.
         - Zero or one callsign/SSID separators are present.
         - SSID, if present, is numeric and within the valid range.

        :param str call: The callsign to be validated.
        :param bool base_only: If `True`, the callsign will be validated as
            one without an SSID, such that a callsign *with* an SSID will be
            considered invalid; if `False`, an SSID may be present.
        :returns: `True` if the callsign is valid; `False` otherwise.
        :rtype: bool
        """
        if not base_only:
            parts = call.split('-')
            if len(parts) > 2:
                return False
            if len(parts) == 2:
                if not parts[1].isdigit():
                    return False
                ssid = int(parts[1])
                if ssid > 15:
                    return False
                call = parts[0]
        return 2 <= len(call) <= ALEN and call.isalnum()

    @property
    def call(self):
        """
        Retrieve the callsign (only) for this address. Readonly.

        :returns: The callsign, without SSID.
        :rtype: str
        """
        return self._call

    @property
    def ssid(self):
        """
        Retrieve the SSID for this address. Readonly.

        :returns: The SSID.
        :rtype: int
        """
        return self._ssid

    @property
    def repeater(self):
        """
        Determine whether or not this is a repeater address. Readonly.

        :returns: `True` if this is a repeater address; `False` otherwise.
        :rtype: bool
        """
        return self._repeater

    @property
    def has_been_repeated(self):
        """
        Determine whether or not this repeater address has been repeated.

        The getter returns `True` if this address has been repeated; `False`
        otherwise.

        The setter takes a `bool` value, and raises :class:`TypeError` if an
        attempt is made to set this property for a non-repeater address.
        """
        if not self._repeater:
            raise TypeError(
                'has_been_repeated not valid for non-repeater address')
        return self._has_been_repeated

    @has_been_repeated.setter
    def has_been_repeated(self, value):
        if not self._repeater:
            raise TypeError(
                'Cannot set has_been_repeated on non-repeater address')
        self._has_been_repeated = value

    @property
    def command_response(self):
        """
        Determine whether or not the command/response bit is set for this
        non-repeater address.

        The getter returns `True` if the command/response bit is set; `False`
        otherwise.

        The setter takes a `bool` value, and raises :class:`TypeError` if an
        attempt is made to set this property for a repeater address.
        """
        if self._repeater:
            raise TypeError(
                'command_response not valid for repeater address')
        return self._command_response

    @command_response.setter
    def command_response(self, value):
        if self._repeater:
            raise TypeError('Cannot set command_response on repeater address')
        self._command_response = value

    def pack(self):
        """
        Pack this :class:`Address` instance into an encoded byte sequence.

        :returns: Encoded byte sequence for this :class:`Address`.
        :rtype: bytes
        """
        b = bytearray(AXLEN)
        for i, c in enumerate(self._call):
            b[i] = ord(c) << 1
        for p in range(i + 1, ALEN):
            b[p] = ord(' ') << 1
        b[ALEN] = self._ssid << 1
        if self._repeater:
            if self._has_been_repeated:
                b[ALEN] |= REPEATED
        else:
            if self._command_response:
                b[ALEN] |= CMDRESP
        b[ALEN] |= RESERVED
        return bytes(b)

    @classmethod
    def unpack(cls, buffer, repeater=False):
        """
        Unpack the encoded byte sequence into a new :class:`Address` instance.

        The `repeater` argument specifies whether the byte sequence represents
        a repeater or non-repeater address.

        :param buffer: Encoded byte sequence.
        :type buffer: bytes or bytearray
        :param bool repeater: Whether or not this address represents a
            repeater address.
        :returns: A new Address instance.
        :rtype: Address
        :raises ValueError: if the encoded information results in an invalid
            callsign.
        """
        call = ""
        for i in range(0, ALEN):
            b = buffer[i]
            c = (b >> 1) & 0x7F
            if c != ord(' '):
                call += chr(c)
        if not cls.valid_call(call, True):
            raise ValueError('Invalid callsign')
        ssid = (buffer[ALEN] & SSID) >> 1
        addr = cls(call, ssid, repeater)
        if repeater:
            addr.has_been_repeated = (buffer[ALEN] & REPEATED) != 0
        else:
            addr.command_response = (buffer[ALEN] & CMDRESP) != 0
        return addr


class Control:
    """
    The control field for an AX.25 frame.

    This includes the frame type, the poll/final indicator, and the send and
    receive sequence numbers. At this time, only modulo 8 (single octet)
    control fields are supported.

    :param FrameType frame_type: Type of the associated :class:`Frame`.
    :param bool poll_final: State of the poll/final indicator.
    :param int recv_seqno: Receive sequence number.
    :param int send_seqno: Send sequence number.
    """
    def __init__(
            self, frame_type, poll_final=False, recv_seqno=0, send_seqno=0):
        self._frame_type = frame_type
        self._poll_final = poll_final
        self._recv_seqno = recv_seqno
        self._send_seqno = send_seqno

    def __repr__(self):
        fmt = 'Control(type: {}, poll_final: {}'
        args = [self._frame_type.name, self._poll_final]
        if self._frame_type.is_I() or self._frame_type.is_S():
            fmt += ', recv_seqno: {}'
            args += str(self._recv_seqno)
        if self._frame_type.is_I():
            fmt += ', send_seqno: {}'
            args += str(self._send_seqno)
        fmt += ')'
        return fmt.format(*args)

    def __str__(self):
        control = self.pack()
        return '{:02X}'.format(control)

    def __int__(self):
        return self.pack()

    @property
    def frame_type(self):
        """
        Retrieve the type of the associated frame. Readonly.

        :returns: Type of the frame.
        :rtype: FrameType
        """
        return self._frame_type

    @property
    def poll_final(self):
        """
        Determine whether or not the poll/final bit is set.

        The getter returns `True` if the poll/final bit is set; `False`
        otherwise.

        The setter takes a `bool` value to set or unset the poll/final bit.
        """
        return self._poll_final

    @poll_final.setter
    def poll_final(self, v):
        self._poll_final = v

    @property
    def recv_seqno(self):
        """
        Retrieve or set the receive sequence number.

        The receive sequence number is an `int`, and is valid only on I and S
        frames; a :class:`TypeError` is raised if an attempt is made to
        retrieve or set this value on a U frame.
        """
        if self._frame_type.is_U():
            raise TypeError('recv_seqno not valid on U frame')
        return self._recv_seqno

    @recv_seqno.setter
    def recv_seqno(self, v):
        if self._frame_type.is_U():
            raise TypeError('Cannot set recv_seqno on U frame')
        self._recv_seqno = v

    @property
    def send_seqno(self):
        """
        Retrieve or set the send sequence number.

        The send sequence number is an `int`, and is valid only on I frames;
        a :class:`TypeError` is raised if an attempt is made to retrieve or
        set this value on an S or U frame.
        """
        if self._frame_type.is_S():
            raise TypeError('send_seqno not valid on S frame')
        if self._frame_type.is_U():
            raise TypeError('send_seqno not valid on U frame')
        return self._send_seqno

    @send_seqno.setter
    def send_seqno(self, v):
        if self._frame_type.is_S():
            raise TypeError('Cannot set send_seqno on S frame')
        if self._frame_type.is_U():
            raise TypeError('Cannot set send_seqno on U frame')
        self._send_seqno = v

    def pack(self):
        """
        Pack this :class:`Control` instance into an encoded value.

        :returns: Encoded value for this :class:`Control`.
        :rtype: int
        :raises ValueError: if the frame type is not set
            (i.e. it is :py:const:`FrameType.UNK`).
        """
        if self._frame_type is FrameType.UNK:
            raise ValueError('Unknown frame type')
        control = self._frame_type.value
        if self._poll_final:
            control |= PF
        if self._frame_type.is_I() or self._frame_type.is_S():
            control |= (self._recv_seqno << NRS)
        if self._frame_type.is_I():
            control |= (self._send_seqno << NSS)
        return control

    @classmethod
    def unpack(cls, control):
        """
        Unpack the encoded value into a new :class:`Control` instance.

        Values for the poll/final bit and receive and send sequence numbers are
        determined based upon the frame type.

        :param int control: Encoded value.
        :returns: A new Control instance.
        :rtype: Control
        :raises ValueError: if the frame type is invalid.
        """
        # Determine frame type first
        ft = FrameType.UNK
        if (control & 0x01) == 0:  # I frame
            ft = FrameType.I
        elif (control & 0x02) == 0:  # S frame
            # May raise ValueError if type is invalid
            ft = FrameType(control & 0x0F)
        else:  # U frame
            # May raise ValueError if type is invalid
            ft = FrameType(control & ~PF)
        # Remaining fields, based on frame type
        pf = (control & PF) != 0
        if ft.is_I() or ft.is_S():
            nr = (control & NR) >> NRS
        else:
            nr = 0
        if ft.is_I():
            ns = (control & NS) >> NSS
        else:
            ns = 0
        return cls(ft, pf, nr, ns)


class Frame:
    """
    A complete AX.25 frame, excluding the flag and FCS fields.

    This includes the address field and control field, and the protocol
    identifier and information field where present.

    :param dst: Destination address. Required.
    :type dst: Address or str
    :param src: Source address. Required.
    :type src: Address or str
    :param via: List of Via addresses. Optional.
    :type via: list[Address or str] or None
    :param Control control: Control field. Required.
    :param int pid: Protocol Identifier. Valid only for I and UI frames.
    :param data: Data for information field. Valid only for I, UI, FRMR, XID
        and TEST frames.
    :type data: bytes or bytearray or None
    :raises TypeError: if any provided field has an invalid type.
    :raises ValueError: if data is provided for an invalid frame type, or if
        the data field is too long.
    """

    def __init__(self, dst, src, via=None, control=None, pid=0, data=None):
        # Addressing first
        def check_subfield(addr):
            if isinstance(addr, Address):
                return addr
            elif isinstance(addr, str):
                return Address(addr)
            else:
                raise TypeError('Invalid address field')
        self._dst = check_subfield(dst)
        self._src = check_subfield(src)
        if via:
            if not isinstance(via, (list, tuple)):
                raise TypeError('Invalid via')
            self._via = tuple(check_subfield(v) for v in via)
        else:
            self._via = None
        # Control field
        if isinstance(control, Control):
            self._control = control
        elif isinstance(control, int):
            self._control = Control.unpack(control)
        else:
            raise TypeError('Invalid control field')
        # Protocol identifier, if present
        ft = self._control.frame_type
        if self._has_pid(ft):
            self._pid = pid
        else:
            self._pid = 0
        # Data, if present
        if self._info_allowed(ft):
            if data is not None:
                if not isinstance(data, (bytearray, bytes)):
                    raise TypeError('Data field must be bytes or bytearray')
                elif len(data) > 256:
                    raise ValueError('Data field too long')
        elif data is not None:
            raise ValueError('Data field not valid for frame type')
        self._data = data

    def __bytes__(self):
        return self.pack()

    @staticmethod
    def _has_pid(ft):
        return ft is FrameType.I or ft is FrameType.UI

    @staticmethod
    def _info_allowed(ft):
        return ft in (
            FrameType.I,
            FrameType.UI,
            FrameType.FRMR,
            FrameType.XID,
            FrameType.TEST)

    @property
    def dst(self):
        """
        Retrieve the destination address for this frame. Readonly.

        :returns: Destination address.
        :rtype: Address
        """
        return self._dst

    @property
    def src(self):
        """
        Retrieve the source address for this frame. Readonly.

        :returns: Source address.
        :rtype: Address
        """
        return self._src

    @property
    def via(self):
        """
        Retrieve the list of Via addresses for this frame. Readonly.

        :returns: List of Via addresses.
        :rtype: list[Address] or None
        """
        return self._via

    @property
    def control(self):
        """
        Retrieve the control field for this frame. Readonly.

        :returns: Control field.
        :rtype: int
        """
        return self._control

    @property
    def pid(self):
        """
        Retrieve the Protocol Identifier for this frame. Readonly.

        :returns: Protocol identifier, or 0 if PID is not permitted for this
            frame type.
        :rtype: int
        """
        # Value will already be zero if pid not allowed for frame type
        return self._pid

    @property
    def data(self):
        """
        Retrieve the information field for this frame. Readonly.

        :returns: Information field data, or None if the information field is
            not permitted for this frame type.
        :rtype: bytes or None
        """
        # Value will already be None if data not allowed for frame type
        return self._data

    def pack(self):
        """
        Pack this :class:`Frame` instance into an encoded byte sequence.

        :returns: Encoded byte sequence for this :class:`Frame`.
        :rtype: bytes
        """
        b = bytearray()
        # Basic address fields
        b.extend(self._dst.pack())
        b.extend(self._src.pack())
        # Repeater addresses
        if self._via:
            for v in self._via:
                b.extend(v.pack())
        b[-1] |= HDLC_AEB
        # Control byte
        b.append(self._control.pack())
        # Protocol identifier, if required
        ft = self._control.frame_type
        if self._has_pid(ft):
            b.append(self._pid)
        if self._info_allowed(ft):
            if self._data:
                b.extend(self._data)
        return bytes(b)

    @classmethod
    def unpack(cls, buffer):
        """
        Unpack the encoded byte sequence into a new :class:`Frame` instance.

        :param buffer: Encoded byte sequence.
        :type buffer: bytes or bytearray
        :returns: A new Frame instance.
        :rtype: Frame
        :raises ValueError: if any encoded address results in an invalid
            callsign.
        """
        # Basic address fields
        dst = Address.unpack(buffer[OFF_DST:OFF_DST + AXLEN])
        src = Address.unpack(buffer[OFF_SRC:OFF_SRC + AXLEN])
        # Repeater addresses
        via = []
        offset = OFF_VIA
        end = (buffer[AXLEN + ALEN] & HDLC_AEB)
        if not end:
            while not end:
                via.append(
                    Address.unpack(buffer[offset:offset + AXLEN], True))
                end = buffer[offset + ALEN] & HDLC_AEB
                offset += AXLEN
        # Control byte
        control = Control.unpack(buffer[offset])
        offset = offset + 1
        # PID, if there is one
        ft = control.frame_type
        if cls._has_pid(ft):
            pid = buffer[offset]
            offset = offset + 1
        else:
            pid = 0
        # Data, if there is any
        if cls._info_allowed(ft):
            data = buffer[offset:]
        else:
            data = None

        return cls(dst, src, via, control, pid, data)
