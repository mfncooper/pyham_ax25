# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
NET/ROM Routing Table Update Structure

Structure definitions together with methods to pack and unpack native NET/ROM
routing table updates. Provides the capabilities for, for example, decoding
NET/ROM routing table update packets in programs such as 'listen'.

Protocol reference:
  https://packet-radio.net/wp-content/uploads/2017/04/netrom1.pdf
"""

import ax25

# Destination offsets
OFF_CALLSIGN = 0
OFF_MNEMONIC = ax25.AXLEN
OFF_NEIGHBOR = ax25.AXLEN + ax25.ALEN
OFF_QUALITY  = ax25.AXLEN + ax25.ALEN + ax25.AXLEN

MNEM_LEN = 6
DEST_SIZE = ax25.AXLEN + MNEM_LEN + ax25.AXLEN + 1


class Destination:
    """
    A single destination element of a routing update.

    This comprises identifiers for the node, along with information on its
    best-quality neighbor.

    :param callsign: Callsign of the destination.
    :type callsign: Address or str
    :param str mnemonic: Mnemonic for the destination.
    :param neighbor: Best-quality neighbor for the destination.
    :type neighbor: Address or str
    :param int quality: Quality of the best-quality neighbor.
    :raises TypeError: if an address is of an invalid type.
    :raises ValueError: if either the mnemonic value or the quality value is
        invalid or out of range.
    """
    def __init__(self, callsign, mnemonic, neighbor, quality):
        # This is copied from Frame.check_subfield; need a common function
        def check_address(addr):
            if isinstance(addr, ax25.Address):
                return addr
            elif isinstance(addr, str):
                return ax25.Address(addr)
            else:
                raise TypeError('Invalid address field')
        self._callsign = check_address(callsign)
        self._neighbor = check_address(neighbor)
        if not (isinstance(mnemonic, str) and 0 < len(mnemonic) <= MNEM_LEN):
            raise ValueError('Invalid mnemonic')
        self._mnemonic = mnemonic
        if not (isinstance(quality, int) and 0 <= quality <= 255):
            raise ValueError('Invalid quality value')
        self._quality = quality

    def __repr__(self):
        return ('Destination(callsign: {}, mnemonic: {}, neighbor: {},'
                ' quality: {})'.format(
                    self._callsign, self._mnemonic, self._neighbor,
                    self._quality))

    def __str__(self):
        return '{} ({}) -> {} ({})'.format(
            self._callsign, self._mnemonic, self._neighbor, self._quality)

    @property
    def callsign(self):
        """
        Retrieve the callsign of the destination. Readonly.

        :returns: Destination callsign.
        :rtype: Address
        """
        return self._callsign

    @property
    def mnemonic(self):
        """
        Retrieve the mnemonic for the destination. Readonly.

        :returns: Destination's mnemonic.
        :rtype: str
        """
        return self._mnemonic

    @property
    def best_neighbor(self):
        """
        Retrieve the best-quality neighbor for the destination. Readonly.

        :returns: The best-quality neighbor.
        :rtype: Address
        """
        return self._neighbor

    @property
    def best_quality(self):
        """
        Retrieve the quality of the best-quality neighbor. Readonly.

        :returns: The best-quality neighbor's quality.
        :rtype: int
        """
        return self._quality

    def pack(self):
        """
        Pack this :class:`Destination` instance into an encoded byte sequence.

        :returns: Encoded byte sequence for this :class:`Destination`.
        :rtype: bytes
        """
        b = bytearray(DEST_SIZE)
        b[OFF_CALLSIGN:OFF_CALLSIGN + ax25.AXLEN] = self._callsign.pack()
        b[OFF_MNEMONIC:OFF_MNEMONIC + ax25.ALEN] = \
            self._mnemonic.ljust(ax25.ALEN).encode('utf-8')
        b[OFF_NEIGHBOR:OFF_NEIGHBOR + ax25.AXLEN] = self._neighbor.pack()
        b[OFF_QUALITY] = self._quality
        return bytes(b)

    @classmethod
    def unpack(cls, buffer):
        """
        Unpack the encoded byte sequence into a new :class:`Destination`
        instance.

        :param buffer: Encoded byte sequence.
        :type buffer: bytes or bytearray
        :returns: A new Destination instance.
        :rtype: Destination
        :raises ValueError: if the encoded information contains an invalid
            address.
        """
        callsign = ax25.Address.unpack(
            buffer[OFF_CALLSIGN:OFF_CALLSIGN + ax25.AXLEN])
        mnemonic = bytes(
            buffer[OFF_MNEMONIC:OFF_MNEMONIC + ax25.ALEN]).decode(
                'utf-8').rstrip()
        neighbor = ax25.Address.unpack(
            buffer[OFF_NEIGHBOR:OFF_NEIGHBOR + ax25.AXLEN])
        quality = buffer[OFF_QUALITY]
        return cls(callsign, mnemonic, neighbor, quality)


class RoutingBroadcast:
    """
    A complete routing update broadcast.

    This comprises sender identification along with a list of destinations.

    :param str sender: Mnemonic of the sender.
    :param destinations: List or tuple of destinations.
    :type destinations: list[Destination] or tuple(Destination)
    :raises TypeError: if a destination is of an invalid type.
    :raises ValueError: if the sender is invalid.
    """
    def __init__(self, sender, destinations):
        if not (isinstance(sender, str) and 0 < len(sender) <= MNEM_LEN):
            raise ValueError('Invalid sender')
        self._sender = sender
        if destinations:
            if not isinstance(destinations, (list, tuple)):
                raise TypeError('Invalid destinations')
            for d in destinations:
                if not isinstance(d, Destination):
                    raise TypeError('Invalid destinations')
            self._destinations = tuple(destinations)
        else:
            self._destinations = None

    def __repr__(self):
        if self._destinations:
            destinations = ','.join(map(repr, self._destinations))
            rep = ('RoutingBroadcast(sender: {},'
                   ' destinations: [{}])'.format(self._sender, destinations))
        else:
            rep = 'RoutingBroadcast(sender: {})'.format(self._sender)
        return rep

    @property
    def sender(self):
        """
        Retrieve the sender of the routing broadcast. Readonly.

        :returns: Sender of the routing broadcast.
        :rtype: str
        """
        return self._sender

    @property
    def destinations(self):
        """
        Retrieve the destinations for routing broadcast. Readonly.

        :returns: Sequence of destinations.
        :rtype: tuple(Destination)
        """
        return self._destinations

    def pack(self):
        """
        Pack this :class:`RoutingBroadcast` instance into an encoded byte
        sequence.

        :returns: Encoded byte sequence for this :class:`RoutingBroadcast`.
        :rtype: bytes
        """
        pack_len = 1 + ax25.ALEN
        if self._destinations:
            pack_len += len(self._destinations) * DEST_SIZE
        b = bytearray(pack_len)
        b[0] = 0xFF
        b[1:1 + ax25.ALEN] = self._sender.ljust(ax25.ALEN).encode('utf-8')
        offset = 1 + ax25.ALEN
        if self._destinations:
            for dest in self._destinations:
                b[offset:offset + DEST_SIZE] = dest.pack()
                offset += DEST_SIZE
        return bytes(b)

    @classmethod
    def unpack(cls, buffer):
        """
        Unpack the encoded byte sequence into a new :class:`RoutingBroadcast`
        instance.

        :param buffer: Encoded byte sequence.
        :type buffer: bytes or bytearray
        :returns: A new RoutingBroadcast instance.
        :rtype: RoutingBroadcast
        :raises TypeError: if the byte sequence does not represent a routing
            broadcast (i.e. if the first byte is not 0xFF).
        :raises ValueError: if the encoded information contains an invalid
            address.
        """
        if buffer[0] != 0xFF:
            raise TypeError("Not a routing broadcast")
        sender = bytes(buffer[1:1 + ax25.ALEN]).decode('utf-8')
        destinations = []
        remaining = len(buffer) - ax25.ALEN - 1
        offset = ax25.ALEN + 1
        while remaining:
            destination = Destination.unpack(
                buffer[offset:offset + DEST_SIZE])
            destinations.append(destination)
            offset += DEST_SIZE
            remaining -= DEST_SIZE
        return cls(sender, destinations)
