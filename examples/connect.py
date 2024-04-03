#!/usr/bin/env python3
# =============================================================================
# Copyright (c) 2022-2024 Martin F N Cooper
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
ease with which a simple connected mode application can be constructed on top
of the native Linux AX.25 stack using ax25.socket. In particular, only the
default port is supported in this example application, and vias are not
supported.These are both supported by the ax25.socket package, however, and
would be straightforward to add should someone choose to use this example as
the basis for a more sophisticated application.
"""

import errno
import platform
import queue
import re
import selectors
import socket
import sys
import threading
import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext

import ax25
import ax25.ports
import ax25.socket


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
        self._sock.bind(self._src)
        self._queue_event('status', 'connecting')
        # The initial connect call will return immediately. To wait for the
        # connection to complete, or timeout, we need to use a selector to
        # wait until the socket is writable.
        self._sock.setblocking(False)
        res = self._sock.connect_ex(self._dst)
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


class LogPanel(tkinter.scrolledtext.ScrolledText):
    """
    Scrolling text panel that logs the commands typed by the user, the
    responses from the remote system, and any errors encountered. Each
    is displayed in a different color for easy comprehension.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, bg='black', **kwargs)
        self.tag_config('tag_local', foreground='magenta')
        self.tag_config('tag_remote', foreground='cyan')
        self.tag_config('tag_error', foreground='red')
        self.configure(state=tk.DISABLED)

    def _add_line(self, line, tag):
        self.configure(state=tk.NORMAL)
        self.insert(tk.END, line + '\n', (tag,))
        self.see(tk.END)
        self.configure(state=tk.DISABLED)

    def local(self, line):
        self._add_line(line, 'tag_local')

    def remote(self, line):
        self._add_line(line, 'tag_remote')

    def error(self, line):
        self._add_line(line, 'tag_error')


class InfoBar(ttk.Frame):
    """
    One-line bar that displays the user's callsign, current connection
    status, and a brief indication of how to get help.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self._var_mycall = tk.StringVar()
        lbl_mycall = ttk.Label(
            self, textvariable=self._var_mycall, anchor=tk.W)
        lbl_mycall.grid(column=0, row=0, sticky=tk.W)

        self._var_connection = tk.StringVar()
        lbl_connection = ttk.Label(
            self, textvariable=self._var_connection, anchor=tk.CENTER)
        lbl_connection.grid(column=1, row=0, sticky=tk.E + tk.W)

        self._var_help_info = tk.StringVar()
        lbl_help_info = ttk.Label(
            self, textvariable=self._var_help_info, anchor=tk.E)
        lbl_help_info.grid(column=2, row=0, sticky=tk.E)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, uniform='col')
        self.grid_columnconfigure(1, weight=1, uniform='col')
        self.grid_columnconfigure(2, weight=1, uniform='col')

    def set_mycall(self, call):
        self._var_mycall.set('My Call: {}'.format(call))

    def set_connection(self, call):
        if call:
            connection = 'Connected to {}'.format(call)
        else:
            connection = 'Not connected'
        self._var_connection.set(connection)

    def set_help_info(self, info):
        self._var_help_info.set(info)


class Application(tk.Tk):
    """
    Main application, creating the UI, responding to commands, and managing
    incoming data. Connector instances are created as required.
    """
    _CMD_PATTERN = re.compile(r"""^:(?P<cmd>[a-z])\s*(?:(?P<args>\S.*))?$""")
    _ALARM_PERIOD = 100  # milliseconds to wait between alarms

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._alarm = None
        self._connected = False
        self._connector = None
        self._mycall = None
        self._destination = None
        self._line_remains = ''

        self.title("AX.25 Socket Connected Mode Example")
        self.geometry("800x600")

        # Main application container
        container = ttk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Log panel with scrollbar
        self._log = LogPanel(container)
        self._log.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Info bar
        self._info_bar = InfoBar(container)
        self._info_bar.pack(fill=tk.X, expand=False, padx=5)

        # Text entry field
        self._var_entry = tk.StringVar()
        self._ent_entry = ttk.Entry(container, textvariable=self._var_entry)
        self._ent_entry.pack(
            side=tk.BOTTOM, fill=tk.X, expand=False, padx=5, pady=5)
        self._ent_entry.bind('<Return>', self._handle_line_entry)

        # Use callsign of first port in axports as an initial value for
        # My Call. The user can change this with the :m command.
        port_info = ax25.ports.PortInfo()
        port_info.load()
        self._mycall = port_info.first_port().callsign

        # Set initial values for the info bar
        self._info_bar.set_mycall(self._mycall)
        self._info_bar.set_connection(None)
        self._info_bar.set_help_info('Type \':h\' for help')

        # Capture the close button
        self.protocol("WM_DELETE_WINDOW", self._do_cmd_q)

        # Give the focus to the entry widget
        self._ent_entry.focus_set()

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
            self._info_bar.set_connection(self._destination)
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
            self._info_bar.set_connection(None)
            self._log.local('Disconnected')
        else:
            self._log.local('Unknown status: {}'.format(status))
        if reset:
            if self._alarm:
                self.after_cancel(self._alarm)
                self._alarm = None
            self._connected = False
            self._destination = None
            self._connector = None

    def _gather_lines(self, data):
        """
        Incoming data generally does not arrive a complete line at a time,
        so we need to gather up data until we have complete lines to send
        to the log.
        """
        if not isinstance(data, str):
            data = data.decode('utf-8')
        parts = data.split('\r')
        if len(self._line_remains):
            parts[0] = self._line_remains + parts[0]
            self._line_remains = ""
        if data[-1] != '\r':
            self._line_remains = parts[-1]
        del parts[-1]
        for part in parts:
            self._log.remote(part)

    def _process_events(self):
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
                self._gather_lines(data)
        self._alarm = self.after(self._ALARM_PERIOD, self._process_events)

    def _do_cmd_c(self, args):
        """ Connect command """
        if self._connected:
            self._log.error('Already connected')
            return
        if len(args) != 1:
            self._log.error('You must provide a callsign to connect to')
            return
        self._destination = args[0]
        self._alarm = self.after(self._ALARM_PERIOD, self._process_events)
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
            self.after_cancel(self._alarm)
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
        self._info_bar.set_mycall(self._mycall)

    def _do_cmd_q(self, args=None):
        """ Quit command """
        if self._connected:
            self._do_cmd_d([])
        self.destroy()

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
            self._log.error('Unknown command: {}'.format(command))

    def _handle_line_entry(self, event):
        """
        Determine whether a line entered by the user is a command, and, if so,
        hand it off to be processed as such. Otherwise, send the entered text
        to the destination, if connected, and echo it in the log.
        """
        text = self._ent_entry.get()
        self._var_entry.set('')
        m = self._CMD_PATTERN.match(text)
        if m:
            self._handle_command(m['cmd'], m['args'])
        else:
            if self._connected:
                self._connector.send((text + '\r').encode('utf-8'))
                self._log.local(text)
            else:
                self._log.error('Not connected')


if platform.system() != 'Linux':
    print("This application is supported only on Linux")
    sys.exit(1)
app = Application()
app.mainloop()
