# =============================================================================
# Copyright (c) 2021-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
AX.25 Sockets

This module provides socket support for the AX.25 protocol. While Python
defines the AX.25 address family, it does not implement support for it, and
will fail with 'bad family' on any attempt to use it.

A socket class with support for AX.25 addressing is provided, as is a
convenience method for sending unproto messages. Callsigns may be provided
as strings or as ax25.Address instances.

Note: The :meth:`receivefrom_into()` method has not been implemented, because
it would require the creation of a new buffer in any case, negating the benefit
of using an already-existing buffer. Use :meth:`receivefrom()` instead.

.. important:: This implementation relies on the Linux AX.25 stack, and will
    not work on any other platform. An exception is raised if an attempt is
    made to use it on a non-Linux platform.
"""

import ctypes
import ctypes.util
import os
import platform
import socket
import struct

import ax25
import ax25.ports


# Address data structures from C

# typedef struct
#   {
#     char ax25_call[7];
#   }
# ax25_address;
_PACK_AX25_ADDRESS = "7s"
_SIZE_AX25_ADDRESS = struct.calcsize(_PACK_AX25_ADDRESS)

# struct sockaddr_ax25
#   {
#     sa_family_t sax25_family;
#     ax25_address sax25_call;
#     int sax25_ndigis;
#   };
_PACK_SOCKADDR_AX25 = "H" + _PACK_AX25_ADDRESS + "I"
_SIZE_SOCKADDR_AX25 = struct.calcsize(_PACK_SOCKADDR_AX25)

# struct full_sockaddr_ax25
#   {
#     struct sockaddr_ax25 fsa_ax25;
#     ax25_address fsa_digipeater[AX25_MAX_DIGIS];
#   };
_AX25_MAX_DIGIS = 8
_PACK_FULL_SOCKADDR_AX25 = _PACK_SOCKADDR_AX25 + (
    _AX25_MAX_DIGIS * _PACK_AX25_ADDRESS)
_SIZE_FULL_SOCKADDR_AX25 = struct.calcsize(_PACK_FULL_SOCKADDR_AX25)


def _packed_addr(call):
    if not isinstance(call, ax25.Address):
        call = ax25.Address(call)
    return call.pack()


def _make_addr(call, digis):
    ndigis = len(digis) if digis else 0
    if ndigis > _AX25_MAX_DIGIS:
        raise ValueError("Too many digipeaters")
    call_bytes = _packed_addr(call)
    full_addr = bytearray(struct.pack(
        _PACK_SOCKADDR_AX25, socket.AF_AX25, call_bytes, ndigis))
    if ndigis > 0:
        for digi in digis:
            full_addr.extend(_packed_addr(digi))
    return bytes(full_addr.ljust(_SIZE_FULL_SOCKADDR_AX25, b'\x00'))


_libc = None
_ports = None


# Requirements for this module to be used:
#   * Running on Linux
#   * Can load the C library (libc)
#   * Can load the axports file
def _check_requirements():
    global _libc, _ports
    # See if we've already checked
    if _libc and _ports:
        return
    # Check that we're running on Linux
    if platform.system() != 'Linux':
        raise ax25.ports.UnsupportedPlatformError(__name__)
    # Load libc
    libc_name = ctypes.util.find_library('c')
    if not libc_name:
        raise OSError("Cannot load required library")
    try:
        libc = ctypes.CDLL(libc_name, use_errno=True)
    except OSError:
        raise OSError("Cannot load required library")
    # Load port config
    ports = ax25.ports.PortInfo()
    ports.load()
    # All good, so set globals
    _libc = libc
    _ports = ports


class Socket(socket.socket):
    """
    Socket support for the AX.25 address family.

    A subclass of the Python socket class that provides support for the AX.25
    address family. The address family is hardcoded to AF_AX25 here, since
    this class is not designed to be used as anything other than an AX.25
    socket. Those socket methods that require addresses as arguments or return
    addresses are overridden; other socket methods are available as normal.

    :param sock_type: Type of socket to create. The default is
        `socket.SOCK_SEQPACKET`, which is the appropriate type for a connected
        session, the primary use case for this class.
    :type sock_type: socket.SocketKind
    """
    def __init__(self, sock_type=socket.SOCK_SEQPACKET):
        _check_requirements()
        super().__init__(socket.AF_AX25, sock_type, 0)

    def accept(self):
        """
        Wait for an incoming connection.

        Returns a new socket representing the connection, and the callsign of
        the client.

        :returns: A tuple of the socket and the callsign.
        :rtype: (Socket, str)
        """
        addr_buf = ctypes.create_string_buffer(_SIZE_FULL_SOCKADDR_AX25)
        addr_len = ctypes.c_int(len(addr_buf))
        res = _libc.accept(self.fileno(), addr_buf, ctypes.byref(addr_len))
        if res < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        # We need to pass in the proto arg while creating the new socket,
        # because there appears to be a bug in copying over the properties,
        # and proto otherwise gets set to a weird and incorrect value.
        new_sock = socket.socket(fileno=res, proto=0)
        fam, call, digis = struct.unpack_from(_PACK_SOCKADDR_AX25, addr_buf)
        return (new_sock, str(ax25.Address.unpack(call)))

    def bind(self, call, port=None):
        """
        Bind the socket to the specified callsign.

        The socket must not already be bound.

        :param call: Callsign to bind to.
        :type call: str or Address
        :param str port: Name of the port to use when binding. Optional.
        :raises ValueError: if an invalid port name is specified.
        :raises OSError: if a bind failure occurs.
        """
        if port:
            port_info = _ports.find_by_portname(port)
            if not port_info:
                raise ValueError("Invalid port")
            port_digis = [port_info.callsign]
        else:
            port_info = _ports.find_by_callsign(str(call))
            if not port_info:
                port_info = _ports.first_port()
                if port_info:
                    port_digis = [port_info.callsign]
                else:
                    port_digis = None
            else:
                port_digis = None
        bind_addr = _make_addr(call, port_digis)
        res = _libc.bind(self.fileno(), bytes(bind_addr), len(bind_addr))
        if res:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def connect(self, call, via=None):
        """
        Connect the socket to a remote station.

        :param call: Callsign of station to connect to.
        :type call: str or Address
        :param via: List of callsigns to use as Via stations. Optional.
        :type via: list[str] or list[Address] or None
        :raises OSError: if a connection failure occurs.
        """
        err = self.connect_ex(call, via)
        if err:
            raise OSError(err, os.strerror(err))

    def connect_ex(self, call, via=None):
        """
        Connect the socket to a remote station.

        Like `connect(call, via)` but return an error code instead of raising
        an exception when a connection failure occurs.

        :param call: Callsign of station to connect to.
        :type call: str or Address
        :param via: List of callsigns to use as Via stations. Optional.
        :type via: list[str] or list[Address] or None
        :returns: `0` on success, or the value of `errno` if a connection
            failure occurs.
        :rtype: int
        """
        bind_addr = _make_addr(call, via)
        res = _libc.connect(self.fileno(), bind_addr, len(bind_addr))
        return ctypes.get_errno() if res else 0

    def recvfrom(self, bufsize):
        """
        Receive data from the socket.

        Like `recv(bufsize)` but also return the sender’s callsign.

        :param int bufsize: Maximum amount of data to be received at once.
        :returns: A tuple of the received data and the sender's callsign.
        :rtype: (bytes, str)
        """
        data_buf = ctypes.create_string_buffer(bufsize)
        addr_buf = ctypes.create_string_buffer(_SIZE_FULL_SOCKADDR_AX25)
        addr_len = ctypes.c_int(len(addr_buf))
        res = _libc.recvfrom(self.fileno(), data_buf, bufsize, 0, addr_buf,
                             ctypes.byref(addr_len))
        if res < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        fam, call, digis = struct.unpack_from(_PACK_SOCKADDR_AX25, addr_buf)
        return (bytes(data_buf), str(ax25.Address.unpack(call)))

    def sendto(self, data, call, via=None):
        """
        Send data to the socket.

        The socket should not be connected to a remote socket, since the
        destination is specified by the callsign.

        :param bytes data: Data to be sent.
        :param call: Callsign of destination.
        :type call: str or Address
        :param via: List of callsigns to use as Via stations. Optional.
        :type via: list[str] or list[Address] or None
        :returns: Number of bytes sent.
        :rtype: int
        """
        addr = _make_addr(call, via)
        count = _libc.sendto(
            self.fileno(), data, len(data), 0, addr, len(addr))
        return count


def send_unproto(src, dst, data, via=None, port=None):
    """
    Convenience function for sending an unproto message.

    This function encapsulates the creation and shutdown of the socket around
    the sending of an unproto message.

    :param src: Callsign of sender.
    :type src: str or Address
    :param dst: Callsign of destination.
    :type dst: str or Address
    :param bytes data: Data to send.
    :param via: List of callsigns to use as Via stations. Optional.
    :type via: list[str] or list[Address] or None
    :param str port: Port to use to send this message. Optional.
    :returns: Number of bytes sent.
    :rtype: int
    """
    with Socket(socket.SOCK_DGRAM) as sock:
        sock.bind(src, port)
        count = sock.sendto(data.encode('utf-8'), dst, via)
    return count
