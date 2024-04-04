#!/usr/bin/env python3
# =============================================================================
# Copyright (c) 2021-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
AX.25 Sockets Example - Connect

A terminal application along the lines of the Linux axcall utility, providing
simple connected mode capability and demonstrating the use of the ax25.socket
package.

Few commands and options are provided, since the focus is on illustrating the
ease with which a connected mode application can be constructed on top of the
native Linux AX.25 stack.
"""

import errno
import queue
import re
import selectors
import socket
import threading
import urwid

import ax25
import ax25.ports
import ax25.socket


palette = [
    ('header_text', 'black', 'white'),
    ('log_text_loc', 'dark magenta', 'black'),
    ('log_text_rem', 'dark cyan', 'black'),
    ('log_text_err', 'dark red', 'black'),
    ('entry_text', 'black', 'light gray')
]


class Connector:
    """
    Encapsulation of all of the socket-related code, simplifying its use from
    the UI. A client of this class need only create an instance with which to
    connect, and then connect and disconnect as appropriate. Incoming data and
    status updates are added to an event queue, which the client should check
    periodically. Outgoing data may be sent at will. Note that instances of
    this class are not reusable.
    """
    _CON_TIMEOUT = 10  # Seconds to wait for connection
    _BUF_LEN = 512  # Buffer length for socket i/o

    def __init__(self):
        self._sock = ax25.socket.Socket()
        self._queue = queue.Queue()
        self._active = True

    @property
    def event_queue(self):
        return self._queue

    def _queue_event(self, kind, data):
        self._queue.put((kind, data))

    def _receive_data(self):
        """
        Retrieves incoming data, using selectors to wait until the socket
        is ready to be read. Data is posted to the queue for the main thread
        to consume.
        """
        with selectors.DefaultSelector() as sel:
            sel.register(self._sock, selectors.EVENT_READ)
            while True:
                events = sel.select()
                for key, mask in events:
                    try:
                        data = self._sock.recv(self._BUF_LEN)
                    except OSError as e:
                        if e.errno != errno.ENOTCONN:  # Connection closed
                            raise
                        self._queue_event('status', 'disconnected')
                        data = None
                    if not data:
                        self._active = False
                        return
                    self._queue_event('data', data)

    def __call__(self):
        """
        Runs the background thread to start the connection and receive all
        incoming data. Status updates and data are posted to a queue, from
        which they can be accessed by the main thread.
        """
        self._sock.bind(self._src)  # FIXME: port, etc.
        self._queue_event('status', 'connecting')
        # The initial connect call will return immediately. To wait for the
        # connection to complete, or timeout, we need to use a selector to
        # wait until the socket is writable.
        self._sock.setblocking(False)
        res = self._sock.connect_ex(self._dst)  # FIXME: via, etc.
        if res == errno.EINPROGRESS:
            with selectors.DefaultSelector() as sel:
                sel.register(self._sock, selectors.EVENT_WRITE)
                events = sel.select(self._CON_TIMEOUT)
                if not events:
                    self._queue_event('status', 'connect-timeout')
                    return
        elif res != 0:
            self._queue_event('status', 'connect-failure')
            return
        self._queue_event('status', 'connected')
        while self._active:
            self._receive_data()

    def connect(self, src, dst, via=None, port=None):
        """
        Called from the main thread to start the connection, spinning up the
        thread that will be used to connect and receive data.
        """
        self._src = src
        self._dst = dst
        self._via = via
        self._port = port
        name = '{}: {} -> {}'.format(port, str(src), str(dst))
        self.thread = threading.Thread(target=self, name=name)
        self.thread.start()

    def disconnect(self):
        """
        Called from the main thread to disconnect, shut down the thread that
        is receiving data, and close the socket.
        """
        self._queue_event('status', 'disconnecting')
        self._active = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
        except OSError:
            pass
        finally:
            self._sock = None
        self._queue_event('status', 'disconnected')

    def send(self, data):
        """
        Called from the main thread to send data over the connection.
        """
        if self._sock:
            self._sock.send(data)


class Header(urwid.WidgetWrap):
    """
    Header bar for the top of the window. The header shows My Call (left),
    callsign of destination (center), and basic help info (right).
    """
    def __init__(self):
        self._left = urwid.Text('', 'left')
        self._center = urwid.Text('', 'center')
        self._right = urwid.Text('', 'right')
        widget = urwid.AttrMap(urwid.Padding(urwid.Columns([
            urwid.Filler(self._left),
            urwid.Filler(self._center),
            urwid.Filler(self._right)
        ], box_columns=[0, 1, 2]), left=1, right=1), 'header_text')
        super().__init__(widget)

    def set_mycall(self, call):
        self._left.set_text('My Call: {}'.format(call))

    def set_connection(self, call):
        if call:
            connection = 'Connected to {}'.format(call)
        else:
            connection = 'Not connected'
        self._center.set_text(connection)

    def set_info(self, text):
        self._right.set_text(text)


class LogPanel(urwid.WidgetWrap):
    """
    Panel comprising the main part of the terminal window, showing all input,
    output, and error messages (each in different colors). This panel is
    scrollable.
    """
    def __init__(self):
        self._log = urwid.SimpleListWalker([])
        self._list = urwid.ListBox(self._log)
        super().__init__(self._list)

    def _append(self, line, attr):
        text = urwid.Text(line)
        if type(line) is str:
            text = urwid.AttrMap(text, attr)
        self._log.append(text)
        self._list.set_focus(len(self._log) - 1, 'above')

    def local(self, line):
        self._append(line, 'log_text_loc')

    def remote(self, line):
        self._append(line, 'log_text_rem')

    def error(self, line):
        self._append(line, 'log_text_err')


class LineEntry(urwid.Edit):
    """
    An extension of the standard urwid Edit that emits a complete line when
    Enter is pressed, and then clears its contents.
    """
    signals = ['line_entry']

    def keypress(self, size, key):
        super().keypress(size, key)
        if key != 'enter':
            return key
        text = self.get_edit_text().strip()
        self.set_edit_text("")
        self._emit('line_entry', text)


class Application:
    """
    Main application, creating the UI, responding to commands, and managing
    incoming data. Connector instances are created as required.
    """
    _CMD_PATTERN = re.compile(r"""^:(?P<cmd>[cdhmq])\s*(?:(?P<args>\S.*))?$""")
    _ALARM_PERIOD = 0.1  # seconds to wait between alarms

    def __init__(self):
        self._palette = palette
        self._loop = None
        self._alarm = None
        self._connected = False
        self._mycall = None
        self._destination = None
        self._connector = None
        # Use callsign of first port in axports as a default
        port_info = ax25.ports.PortInfo()
        port_info.load()
        self._mycall = port_info.first_port().callsign

    def _create_widgets(self):
        """
        The application comprises three widgets: a header bar at the top, a
        log window filling the bulk of the window, and an entry line at the
        bottom that the user interacts with.
        """
        self._log = LogPanel()
        self._entry = LineEntry(caption="> ", edit_text="")
        urwid.connect_signal(
            self._entry, 'line_entry', self._handle_line_entry)

        self._header = Header()
        self._footer = urwid.AttrMap(self._entry, 'entry_text')
        self._frame = urwid.Frame(
            self._log,
            header=self._header,
            footer=self._footer,
            focus_part='footer')

        self._header.set_mycall(self._mycall)
        self._header.set_connection(None)
        self._header.set_info("Type ':h' for help")

        return self._frame

    def _update_status(self, status):
        """
        Handle status updates from the connector, telling the user what's
        going on, and updating connection status.
        """
        reset = False
        if status == 'connecting':
            self._log.local('Connecting to {} ...'.format(self._destination))
        elif status == 'connected':
            self._connected = True
            self._header.set_connection(self._destination)
            self._log.local('Connected to {}'.format(self._destination))
        elif status == 'connect-timeout':
            self._log.error('Connection attempt timed out')
            reset = True
        elif status == 'connect-failure':
            self._log.error('Connection attempt failed')
            reset = True
        elif status == 'disconnecting':
            self._log.local('Disconnecting ...')
        elif status == 'disconnected':
            reset = True
            self._header.set_connection(None)
            self._log.local('Disconnected')
        else:
            self._log.local('Unknown status: {}'.format(status))
        if reset:
            if self._alarm:
                self._loop.remove_alarm(self._alarm)
                self._alarm = None
            self._connected = False
            self._destination = None
            self._connector = None

    def _process_events(self, loop, data):
        """
        Check for and process any events on the connector queue. These might
        be either status updates or incoming data. This method is called on
        a periodic basis, using an urwid alarm.
        """
        if not self._connector:
            return
        queue = self._connector.event_queue
        while not queue.empty():
            (kind, data) = queue.get()
            if kind == 'status':
                self._update_status(data)
            else:
                lines = data.decode('utf-8').splitlines()
                for line in lines:
                    self._log.remote(line)
        self._alarm = self._loop.set_alarm_in(
            self._ALARM_PERIOD, self._process_events)

    def _do_cmd_c(self, args):
        """ Connect command """
        if self._connected:
            self._log.error('Already connected')
            return
        if len(args) != 1:
            self._log.error('You must provide a callsign to connect to')
            return
        self._destination = args[0]
        self._alarm = self._loop.set_alarm_in(
            self._ALARM_PERIOD, self._process_events)
        self._connector = Connector()
        self._connector.connect(self._mycall, self._destination)

    def _do_cmd_d(self, args):
        """ Disconnect command """
        if not self._connected:
            self._log.error('Not connected')
            return
        if len(args) > 0:
            self._log.error('No arguments for disconnect')
            return
        self._log.local('Disconnecting')
        self._connector.disconnect()
        if self._alarm:
            self._loop.remove_alarm(self._alarm)
            self._alarm = None

    def _do_cmd_h(self, args):
        """ Help command """
        help = [
            'Commands:',
            '  :c <call>   Connect',
            '  :d          Disconnect',
            '  :h          print Help',
            '  :m <call>   set My Call',
            '  :q          Quit'
        ]
        for line in help:
            self._log.local(line)

    def _do_cmd_m(self, args):
        """ My Call command """
        if len(args) != 1:
            self._log.error('Must provide a callsign to set My Call')
            return
        self._mycall = args[0]
        self._header.set_mycall(self._mycall)

    def _do_cmd_q(self, args):
        """ Quit command """
        if self._connected:
            self._do_cmd_d([])
        raise urwid.ExitMainLoop()

    def _handle_command(self, command, args):
        """
        A command has a handler method with a prefix of '_do_cmd_'. Look up
        that method and invoke it if it exists; otherwise report an unknown
        command.
        """
        args = args.split() if args else []
        try:
            getattr(self, '_do_cmd_' + command)(args)
        except AttributeError:
            self._log.error('Unknown command')

    def _handle_line_entry(self, widget, text):
        """
        Determine whether a line entered by the user is a command, and, if so,
        hand it off to be processed as such. Otherwise, send the entered text
        to the destination, if connected, and echo it in the log.
        """
        m = self._CMD_PATTERN.match(text)
        if m:
            self._handle_command(m['cmd'], m['args'])
        else:
            self._log.local(text)
            if self._connected:
                self._connector.send((text + '\r').encode('utf-8'))

    def run(self):
        """ Start the application """
        self._loop = urwid.MainLoop(
            self._create_widgets(),
            palette=self._palette)
        self._loop.run()


app = Application()
app.run()
