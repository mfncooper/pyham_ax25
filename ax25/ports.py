# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
AX.25 Port Information

Methods to query for available AX.25 ports, by interface name, port name, or
callsign. Required to obtain, for example, the AX.25 port name for unproto
frames arriving on a given network interface.

.. important:: This implementation relies on the Linux AX.25 stack, and will
    not work on any other platform. An exception is raised if an attempt is
    made to use it on a non-Linux platform.
"""

import fcntl
import platform
import re
import socket
import struct

import ax25

#
# Constants missing from standard Python modules
#

# Socket configuration controls.
SIOCGIFFLAGS  = 0x8913  # get flags
SIOCGIFHWADDR = 0x8927  # Get hardware address

# Maximum length of interface name
IFNAMSIZ = 16

# Standard interface flags (netdevice->flags).
IFF_UP = 0x1

# ARP protocol HARDWARE identifiers.
ARPHRD_AX25 = 3    # AX.25 Level 2

#
# Formats for packing / unpacking structures
#

# ifreq (Get hardware address)
#
# struct ifreq {
#     char ifr_name[IFNAMSIZ]; /* Interface name */
#     struct sockaddr ifr_hwaddr;
# };
_PACK_IFREQ_HWADDR = "16sH14s"

# ifreq (get flags)
#
# struct ifreq {
#    char ifr_name[IFNAMSIZ]; /* Interface name */
#    short           ifr_flags;
# };
_PACK_IFREQ_FLAGS = "16sh"

# struct sockaddr {
#    unsigned short   sa_family;
#    char             sa_data[14];
# };
_PACK_SOCKADDR = "H14s"

#
# RegEx patterns for parsing
#

_AXPORTS_PATTERN = re.compile(r"""
    ^
    (?P<portname>\S+)
    \s+
    (?P<callsign>\S+)
    \s+
    (?P<speed>\d+)
    \s+
    (?P<paclen>\d+)
    \s+
    (?P<window>\d+)
    \s+
    (?P<description>.+)
    $
""", re.VERBOSE)

_AXPORTS_FILE = '/etc/ax25/axports'


class UnsupportedPlatformError(RuntimeError):
    """
    Raised when a Linux-only module is invoked on a non-Linux platform.

    :param str name: Name of the module being used in error.
    """
    def __init__(self, name):
        super().__init__("{} is supported only on Linux".format(name))


class Port:
    """
    Descriptor for an AX.25 port.

    The information in this descriptor is a combination of static data from the
    `axports` file and live interface data from the Linux OS.

    :param str ifname: Network interface name.
    :param str portname: AX.25 port name.
    :param str callsign: Callsign attached to the port.
    :param int speed: Serial line speed between computer and TNC.
    :param int paclen: Maximum packet length to send.
    :param int window: Number of frames to send without an ACK.
    :param str description: User description for this port.
    """
    def __init__(self, ifname, portname, callsign, speed, paclen,
                 window, description):
        self.ifname = ifname
        self.portname = portname
        self.callsign = callsign
        self.speed = int(speed)
        self.paclen = int(paclen)
        self.window = int(window)
        self.description = description

    def __repr__(self):
        v = vars(self)
        kv = [item for k in v for item in (k, v[k])]
        f = ["{}={!r}"] * len(v)
        fs = "{}({})".format(self.__class__.__name__, ", ".join(f))
        return fs.format(*kv)


class PortInfo:
    """
    Centralized access to information about available AX.25 ports.

    The OS is interrogated to determine all currently active AX.25 ports. This
    information is then combined with data from `axports` to form a central
    source of data on available AX.25 ports. Multiple accessors provide
    convenient lookups for different use cases.
    """
    def __init__(self):
        if platform.system() != 'Linux':
            raise UnsupportedPlatformError(__name__)
        self._sock = None
        self._port_info = None

    def load(self):
        """
        Load the data for all available AX.25 ports.

        :returns: `True` if the information was loaded successfully; `False`
            if the information is not available.
        :rtype: bool
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not self._sock:
            # Fail if we can't open a socket
            return False

        call_to_if = {}
        ifnames = self._get_interface_names()
        for ifname in ifnames:
            (family, data) = self._get_interface_info(ifname)
            if family != ARPHRD_AX25:
                continue
            if not self._is_interface_up(ifname):
                continue
            af = ax25.Address.unpack(data)
            call_to_if[str(af)] = ifname

        axports = self._get_axport_info()
        for axport in axports:
            axport.ifname = call_to_if[axport.callsign]

        self._port_info = axports
        return True

    def first_port(self):
        """
        Retrieve the first active port configured in the `axports` file.

        The first configured port is frequently used as a default by AX.25
        applications.

        :returns: The first active AX.25 port, or `None` if there are no
            active ports.
        :rtype: Port or None
        """
        return self._port_info[0] if self._port_info else None

    def find_by_ifname(self, ifname):
        """
        Look up port information based on its interface name.

        :param str ifname: Interface name to look up.
        :returns: The port with this interface name, or `None` if there is no
            such port.
        :rtype: Port or None
        """
        return next(
            (p for p in self._port_info if p.ifname == ifname), None)

    def find_by_portname(self, portname):
        """
        Look up port information based on its port name.

        :param str portname: Port name to look up.
        :returns: The port with this port name, or `None` if there is no
            such port.
        :rtype: Port or None
        """
        return next(
            (p for p in self._port_info if p.portname == portname), None)

    def find_by_callsign(self, callsign):
        """
        Look up port information based on its attached callsign.

        :param str callsign: Callsign to look up.
        :returns: The port with this attached callsign, or `None` if there is
            no such port.
        :rtype: Port or None
        """
        return next(
            (p for p in self._port_info if p.callsign == callsign), None)

    def _get_interface_names(self):
        ifnames = []
        with open("/proc/net/dev", "r") as fp:
            lines = fp.read().splitlines()
        # First 2 lines are headers
        for line in lines[2:]:
            ifnames.append(line[:line.find(':')].strip())
        return ifnames

    def _get_interface_info(self, ifname):
        ifreq = fcntl.ioctl(self._sock.fileno(), SIOCGIFHWADDR,
                            struct.pack(_PACK_IFREQ_HWADDR,
                                        bytes(ifname, 'utf-8')[:15], 0, b''))
        (name, family, data) = struct.unpack(_PACK_IFREQ_HWADDR, ifreq)
        return (family, data)

    def _is_interface_up(self, ifname):
        ifreq = fcntl.ioctl(self._sock.fileno(), SIOCGIFFLAGS,
                            struct.pack(_PACK_IFREQ_FLAGS,
                                        bytes(ifname, 'utf-8')[:15], 0))
        (name, flags) = struct.unpack(_PACK_IFREQ_FLAGS, ifreq)
        return flags & IFF_UP

    def _get_axport_info(self):
        axports = []
        with open(_AXPORTS_FILE, 'r') as fp:
            lines = fp.read().splitlines()
        for line in lines:
            if line.startswith('#'):
                continue
            m = _AXPORTS_PATTERN.match(line)
            if m:
                port = Port(None, m['portname'], m['callsign'], m['speed'],
                            m['paclen'], m['window'], m['description'])
                axports.append(port)
        return axports
