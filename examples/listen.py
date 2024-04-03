#!/usr/bin/env python3
# =============================================================================
# Copyright (c) 2020-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
AX.25 Frame Decoding Example - Listen

A command line application that enables monitoring of AX.25 frames in a manner
similar to that of the 'listen' application available on Linux.

Frames are decoded using the 'ax25' module, and embedded NET/ROM broadcast
data is decoded using the 'ax25.netrom' module. When running under Linux and
on top of the Linux AX.25 protocol stack, the 'ax25.ports' module is used
to identify the incoming port. (Port information is not available via KISS.)

The application supports two different means of acquiring AX.25 packets. On
all platforms, it can connect to software such as Direwolf using KISS, and
receive packets provided to it through that connection. On Linux only, it can
use the native AX.25 protocol stack to receive packets directly. The choice
between these means is made through use of one of the following command line
options:

  -k host:port or --kiss host:port    use KISS via the specified host and port
  -l or --linux                       use Linux AX.25 protocol stack

A subset of the options to the regular Linux 'listen' application is supported,
but as negative options. That is, color, timestamp, and port name are all
enabled by default, but can be turned off if desired. These options are as
follows:

  -c or --no-color    do not color callsigns, etc.
  -p or --no-port     do not include port name
  -t or --no-time     do not include timestamp

Retrieval of AX.25 frames is performed by listen_kiss() or listen_linux(),
depending upon invocation. Decoding of those frames is performed by
print_frame(), and, if the frame includes data, print_frame_data().

Use Ctrl-C to exit the application.
"""

import argparse
import datetime
import platform
import socket
import sys

import ax25
import ax25.netrom

# Missing from 'socket'
ETH_P_AX25 = 2
ETH_P_ALL  = 3


class Color:
    """
    Simple class that provides coloring of values when color is enabled, and
    ignoring of color when it is not. Once an instance is created, the user
    need not be concerned about checking for enabling, or the specific colors
    to be used for different types of values. In addition, values are forced
    to strings here, eliminating the need for the caller to convert first.
    """
    # Color encoding
    CPORT = '\033[92m'
    CCALL = '\033[92m'
    CTIME = '\033[93m'
    COFF  = '\033[0m'

    def __init__(self, enabled):
        if enabled:
            self._color = self._with_color
        else:
            self._color = self._without_color

    def call(self, value):
        return self._color(value, Color.CCALL)

    def port(self, value):
        return self._color(value, Color.CPORT)

    def time(self, value):
        return self._color(value, Color.CTIME)

    def _with_color(self, value, color):
        return color + str(value) + Color.COFF

    def _without_color(self, value, color):
        return str(value)


class Options:
    """
    Simple class that provides 'dot' access to our command line options. The
    boolean values are negated, since the command line options are used to
    disable capabilities, whereas internally we want to know what is enabled.
    """
    def __init__(self, args, host_port):
        self.color = not args.no_color
        self.port = not args.no_port
        self.time = not args.no_time

        self.use_linux = host_port is None
        if host_port:
            self.host = host_port[0]
            self.port = host_port[1]


def get_options():
    """
    Get options from our command line arguments. Only syntax is handled here;
    the legitimacy of options is handled by the caller.
    """
    parser = argparse.ArgumentParser(
        description='Listen for and decode AX.25 packets.',
        epilog='Either --linux or --kiss must be specified.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c', '--no-color',
        action='store_true',
        help='do not color callsigns, etc.')
    parser.add_argument(
        '-p', '--no-port',
        action='store_true',
        help='do not include port name')
    parser.add_argument(
        '-t', '--no-time',
        action='store_true',
        help='do not include timestamp')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-k', '--kiss',
        metavar='host:port',
        help='use KISS via specified host and port')
    group.add_argument(
        '-l', '--linux',
        action='store_true',
        help='use Linux AX.25 protocol stack')
    args = parser.parse_args()

    # Parse and validate host and port for KISS
    host_port = None
    if args.kiss:
        host_port = args.kiss.split(':')
        if (len(host_port) != 2
                or len(host_port[0]) < 1
                or len(host_port[1]) < 1
                or not host_port[1].isdigit()):
            raise ValueError(
                'Must provide <host_name>:<port_number> for KISS connection')
        host_port[1] = int(host_port[1])

    # Create positive options from negative args
    return Options(args, host_port)


def print_frame_data(frame):
    """
    For I or UI frames, print associated data. Text data (0xF0) is printed
    directly, after allowing for unprintable characters. Any NET/ROM broadcast
    data is decoded and printed in a similar manner to the Linux 'listen'
    application.
    """
    if frame.pid == 0xF0:
        print(frame.data.decode('utf-8', 'replace'))
    elif frame.pid == 0xCF and frame.data[0] == 0xFF:
        try:
            rb = ax25.netrom.RoutingBroadcast.unpack(frame.data)
        except Exception:
            # Ignore malformed NET/ROM data
            return
        print("NET/ROM Routing: {}".format(rb.sender))
        if rb.destinations:
            for d in rb.destinations:
                print("   {!s:>9}   {:<6}   {!s:>9}   {:>3}".format(
                    d.callsign, d.mnemonic, d.best_neighbor, d.best_quality))


def print_frame(frame, port, opts):
    """
    Print the AX.25 frame according to specified options. The output format
    is very similar to that of the Linux 'listen' application. For any I or
    UI frames, print_frame_data() is called to decode any associated data.
    """
    color = Color(opts.color)
    line = ""

    if opts.time:
        line += "{} ".format(
            color.time(datetime.datetime.now().strftime('%H:%M:%S')))
    if opts.port and port:
        line += "{} ".format(color.port(port + ':'))
    line += "fm {} to {}".format(color.call(frame.src), color.call(frame.dst))
    via = frame.via
    if via:
        line += " via "
        line += " ".join([color.call(v) for v in via])

    control = frame.control
    ft = control.frame_type
    line += " ctl {}".format(ft.name)
    if not ft.is_U():
        line += "(nr={})".format(control.recv_seqno)
    if ft.is_I():
        line += "(ns={})".format(control.send_seqno)
    if ft is ax25.FrameType.I or ft is ax25.FrameType.UI:
        line += " pid={:02X} len {}".format(frame.pid, len(frame.data))

    print(line)
    if (ft is ax25.FrameType.I or ft is ax25.FrameType.UI):
        print_frame_data(frame)


def extract_from_kiss(data):
    """
    Very simplistic extraction of data from KISS frame. This is not intended
    to be foolproof, just minimally sufficient to allow the application to
    retrieve and successfully decode the majority of packets.
    """
    if not (data[0] == 0xC0 and data[1] == 0x00 and data[-1] == 0xC0):
        return None
    return data[2:-1].replace(
        b'\xDB\xDD', b'\xDB').replace(b'\xDB\xDC', b'\xC0')


def listen_kiss(opts):
    """
    Listen for AX.25 frames and print their contents. A regular socket is
    opened to the host and port specified by the user.
    """
    try:
        sock = socket.create_connection((opts.host, opts.port))
    except OSError:
        print(f"Unable to connect to {opts.host}:{opts.port}")
        sys.exit(1)
    while True:
        data, _ = sock.recvfrom(1024)
        frame_data = extract_from_kiss(data)
        if frame_data:
            frame = ax25.Frame.unpack(frame_data)
            print_frame(frame, None, opts)


def listen_linux(opts):
    """
    Listen for AX.25 frames and print their contents. A raw socket is opened
    to the underlying Linux AX.25 protocol stack. Note that this is only
    possible when the application is run as root.
    """
    try:
        sock = socket.socket(
            socket.PF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_AX25))
    except PermissionError:
        print("You must be root to run listen")
        sys.exit(1)

    if opts.port:
        import ax25.ports
        ports = ax25.ports.PortInfo()
        ports.load()
    port = None

    while True:
        data, addr = sock.recvfrom(1024)
        # Discard leading 0x00 byte before actual frame data
        frame = ax25.Frame.unpack(data[1:])
        if opts.port:
            port = ports.find_by_ifname(addr[0]).portname
        print_frame(frame, port, opts)


# Mainline code
if __name__ == "__main__":
    try:
        opts = get_options()
    except ValueError as e:
        print(f"Invalid arguments: {e}")
        sys.exit(1)
    if opts.use_linux and platform.system() != 'Linux':
        print("Linux option is only available on Linux systems")
        sys.exit(1)
    try:
        if opts.use_linux:
            listen_linux(opts)
        else:
            # Enable colored output on Windows if needed
            if opts.color and platform.system() == 'Windows':
                import os
                os.system('color')
            listen_kiss(opts)
    except KeyboardInterrupt:
        print("\b\b\rThanks for listening!")
        sys.exit(0)
