.. _user_guide:

User Guide
==========

Rather than just lay out the API class by class and method by method, this
User Guide walks through some use cases for the PyHam AX.25 package, starting
from the basics and adding capability as it progresses.

For complete details of the classes and methods, see the
:doc:`API Reference <autoapi/index>`.

Monitoring AX.25 traffic
------------------------

As our first example, we will build up a command line tool that allows
the monitoring of received AX.25 traffic. This will be similar to a
basic version of the Linux AX.25 ``listen`` utility. We'll assume that
packets are coming to us via some means - perhaps a KISS connection to
Direwolf - and we'll take it from there.

First, we need to unpack the packet into something we can work with.

.. code-block:: python

   def print_frame(data):
       frame = ax25.Frame.unpack(data)

Now we have a structured representation of the packet, derived from the
byte sequence we received. Let's print out the source and destination,
just as ``listen`` would do.

.. code-block:: python

   def print_frame(data):
       frame = ax25.Frame.unpack(data)
       line = 'fm {!s} to {!s}'.format(frame.src, frame.dst))
       print(line)

There are a couple of things to note here.

-  The ``src`` and ``dst`` properties of the ``frame`` object each
   provide us with an ``ax25.Address`` instance. With this, we could
   access individual fields of the address, such as base callsign and
   SSID.
-  Calling ``str()`` on an ``ax25.Address`` returns the usual string
   representation of a callsign, complete with any SSID. Since this is
   all we need right now, we use the ``!s`` conversion in the format
   string so that ``str()`` is invoked for us.

With the above, we now have the beginnings of our ``listen`` utility.
We'd see a sequence of lines such at the following on our console.

::

   fm WR6ABD-5 to KU6S-2

Now let's add any 'via' information that might be part of our packet.
This will tell us how the packet is traveling through nodes in the
network.

.. code-block:: python

   def print_frame(data):
       frame = ax25.Frame.unpack(data)
       line = 'fm {!s} to {!s}'.format(frame.src, frame.dst))

       via = frame.via
       if via:
           line += " via "
           line += " ".join([str(v) for v in via])

       print(line)

A couple more things to note here:

-  The ``via`` property of the ``frame`` object provides us with a tuple
   of ``ax25.Address`` instances, one for each repeater in the chain. If
   there are no repeaters, the ``via`` property will return ``None``.
-  We're explicitly invoking ``str()`` here since we're not using
   ``format()``.

Our output might now look like the following.

::

   fm WR6ABD-5 to KU6S-2 via KLPRC3* KBERR

Note the asterisk after one of the repeaters. This indicates that the
packet has been repeated by this repeater. If we'd needed to access this
information from the ``ax25.Address`` instance, we could have done so
using the ``has_been_repeated`` property. However, in our case, it is
sufficient to let ``str()`` render this for us as part of the callsign.

Next we'll add the control information associated with the packet. This
will necessitate looking at the frame type, so that we can determine
which fields might be relevant. This is a slightly larger code fragment,
so let's break it down and look at it in a few isolated pieces before we
add it to our ``print_frame()`` function.

.. code-block:: python

       control = frame.control
       ft = control.frame_type
       line += " ctl {}".format(ft.name)

Things to note here:

-  The ``control`` property gives us structured access to the control
   byte of the frame, in the form of an ``ax25.Control`` instance.
-  The first thing we want to know is the type of the frame, so that we
   can make decisions about its content. The ``frame_type`` property of
   the control instance provides us with us a member of the
   ``ax25.FrameType`` enumeration with which we can make those
   decisions.
-  The names of the members of this enumeration correspond to the
   standard names for the frame types, so we can use that name directly
   in our format string.

The output from the latest version of our ``print_frame()`` might now
look something like this.

   fm WR6ABD-5 to KU6S-2 via KLPRC3\* KBERR ctl UI

Since we now have the frame type, we can selectively show information
that is available only for certain frame types.

.. code-block:: python

       if not ft.is_U():
           line += "(nr={})".format(control.recv_seqno)
       if ft.is_I():
           line += "(ns={})".format(control.send_seqno)
       if ft is ax25.FrameType.I or ft is ax25.FrameType.UI:
           line += " pid={:02X} len={}".format(frame.pid, len(frame.data))

Several things to note here:

-  The ``ax25.FrameType`` enumeration also has member functions that
   allow the determination of the general kind of frame type. This
   conveniently lets us decide what to do without needing to consider
   all of the possible frame types.

   -  ``is_I()`` - Returns ``True`` for an I or Information frame
   -  ``is_S()`` - Returns ``True`` for an S or Supervisory frame
   -  ``is_U()`` - Returns ``True`` for a U or Unnumbered frame

-  Send and receive sequence numbers are available from the control
   instance using the ``send_seqno`` and ``recv_seqno`` properties
   respectively.
-  The Protocol Identifier, or PID, is available using the ``pid``
   property.
-  The data content of the frame, if any, is available using the
   ``data`` property. The data is returned as a ``bytes()`` instance, or
   ``None`` if there is no data.

Here's the latest version of what our output might look like:

::

   fm WR6ABD-5 to KU6S-2 via KLPRC3* KBERR ctl UI pid=F0 len=15

This completes our summary line, so let's take a look at the complete
``print_frame()`` function that we've constructed.

.. code-block:: python

   def print_frame(data):
       frame = ax25.Frame.unpack(data)
       line = 'fm {!s} to {!s}'.format(frame.src, frame.dst))

       via = frame.via
       if via:
           line += " via "
           line += " ".join([str(v) for v in via])

       control = frame.control
       ft = control.frame_type
       line += " ctl {}".format(ft.name)

       if not ft.is_U():
           line += "(nr={})".format(control.recv_seqno)
       if ft.is_I():
           line += "(ns={})".format(control.send_seqno)
       if ft is ax25.FrameType.I or ft is ax25.FrameType.UI:
           line += " pid={:02X} len={}".format(frame.pid, len(frame.data))

       print(line)

In only a few lines of code, we've unpacked an AX.25 packet and
summarized its contents in a manner very similar to the Linux ``listen``
utility.

With a little additional work, we could easily add a bit more of what
the ``listen`` utility provides.

-  Coloring for callsigns. Instead of simply calling ``str()`` on each
   address we could pass it to another function to color it first.
-  Printing packet data. For packets that contain text, identified by a
   PID value of ``0xF0``, we could print out the data on the next line. We'd
   need to ensure that the characters are all printable first, though.

Adding NET/ROM routing table updates
------------------------------------

The ``pyham_ax25`` package includes the capability for unpacking NET/ROM
routing updates, so with our ``print_frame()`` function in hand, we can
very simply add this capability to what we already have.

First, we'll add a couple of lines to the end of our ``print_frame()``
function to determine whether or not the packet is of a type that allows
data, and, if it does, call a new function to print that data.

.. code-block:: python

       if (ft is ax25.FrameType.I or ft is ax25.FrameType.UI):
           print_frame_data(frame)

Now let's put together the beginnings of our new function.

.. code-block:: python

   def print_frame_data(frame):
       if frame.pid == 0xF0:
           print(frame.data.decode('utf-8', 'replace'))
       elif frame.pid == 0xCF:
           rb = ax25.netrom.RoutingBroadcast.unpack(frame.data)

A few notes:

-  While we're looking at the data, we've gone ahead and included
   printing out text data, as mentioned at the end of the previous
   section. When the PID is ``0xF0``, indicating text, we simply decode the
   bytes into a printable string, replacing any unprintable characters.
-  A PID of ``0xCF`` indicates NET/ROM routing table updates. In this case,
   we use the ``ax25.netrom`` module to unpack the data into a
   structured representation that we can use to print the table.

With the structured data in hand, we can now print it out.

.. code-block:: python

           print("NET/ROM Routing: {}".format(rb.sender))
           if rb.destinations:
               for d in rb.destinations:
                   print("   {!s:>9}   {:<6}   {!s:>9}   {:>3}".format(
                       d.callsign, d.mnemonic, d.best_neighbor, d.best_quality))

Again, a few notes:

-  The ``ax25.netrom.RoutingBroadcast`` instance provides us with the
   sender and a tuple of destinations. Each is accessed via a property.
-  Each destination is an instance of ``ax25.netrom.Destination``, and
   has a set of properties representing that destination.
-  The destination callsign and best neighbor are instances of
   ``ax25.Address``, so we use the ``!s`` conversion in the format
   string to obtain the appropriate string representation.
-  The sender and each destination mnemonic are simple strings, and so
   can be printed out directly.

That's it. Here is our completed ``print_frame_data()`` function.

.. code-block:: python

   def print_frame_data(frame):
       if frame.pid == 0xF0:
           print(frame.data.decode('utf-8', 'replace'))
       elif frame.pid == 0xCF:
           rb = ax25.netrom.RoutingBroadcast.unpack(frame.data)
           print("NET/ROM Routing: {}".format(rb.sender))
           if rb.destinations:
               for d in rb.destinations:
                   print("   {!s:>9}   {:<6}   {!s:>9}   {:>3}".format(
                       d.callsign, d.mnemonic, d.best_neighbor, d.best_quality))

With this addition, given an incoming NET/ROM routing table update, the
output from our ``print_frame()`` function might look like the
following.

::

   fm WA6TOW-1 to NODES ctl UI pid=CF len=133
   NET/ROM Routing: PAC
       KF6ANX-5   HILL      KF6ANX-5   192
       KF6ANX-4   JOHN      KF6ANX-4   192
        N6ACK-4   LPRC3      K6JAC-4   146
        N6RZR-5   RDG        K6JAC-4   146
        WA7DG-4   ROSE       K6JAC-4   146
       KI6ZHD-7   SCLARA    KI6UDZ-7   134

Composing an Unproto message
----------------------------

Now we'll turn our attention to the other side of the equation -
creating an AX.25 packet to send out. For a simple use case, we'll
assume that we need to send out an Unproto message, for example as a
beacon or as part of a weekly packet net conversation. Similarly to our
earlier examples, we'll assume that we hand off the completed packets to
some transport mechanism - perhaps a KISS connection to Direwolf.

First, let's define a couple of "constants" so that the rest of our
function is a little more clear.

.. code-block:: python

   UNPROTO_FRAME_TYPE = ax25.FrameType.UI
   UNPROTO_PID = 0xF0

Unproto messages are sent as Unnumbered Information (UI) packets, so we
can define that here. And as we saw earlier, a PID value of ``0xF0`` is used
to specify text content.

Now here's all we need in order to compose our packet.

.. code-block:: python

   def compose_unproto_frame(src_call, dst_call, msg):
       control = ax25.Control(UNPROTO_FRAME_TYPE)
       frame = ax25.Frame(
           dst_call,
           src_call,
           control=control,
           pid=UNPROTO_PID,
           data=msg.encode('utf-8'))
       return frame

A couple of things worth noting:

-  The callsigns, ``src_call`` and ``dst_call``, may be either strings
   or instances of ``ax25.Address``. In essence, this is the inverse of
   our use of ``str()`` in the earlier examples, insofar as passing in a
   string will cause it to be transparently converted to an instance of
   ``ax25.Address`` internally.
-  The data passed to ``ax25.Frame()`` must be an instance of ``bytes``
   or ``bytearray``, so we must encode our message before passing it in.

If we were to hardcode an example of how this could be used, along with
some ``send_frame()`` function to actually send it, we might have:

.. code-block:: python

   src_call = 'K6EAG-2'
   dst_call = 'KU6S-5'
   message = 'Hello net, from Fremont, CA!'
   frame = compose_unproto_frame(src_call, dst_call, message)
   send_frame(frame.pack())

Notice that we call ``pack()`` on the frame instance to obtain the
``bytes()`` we need for actually sending it. We could also just cast the
frame to ``bytes()``, since this would call ``pack()`` behind the
scenes.

If someone were to be monitoring, using our earlier example, when this
was sent, they would see this on their console:

::

   fm K6EAG-2 to KU6S-5 ctl UI pid=F0 len=28
   Hello net, from Fremont, CA!

Retrieving Port information (Linux only)
----------------------------------------

If we were to write our own ``listen`` utility based on the Linux AX.25
stack, we might want to include information on which port each packet is
received on, just as Linux' own ``listen`` utility does. Unfortunately,
doing so is not quite as simple as it should be. For this reason, the
``ax25.ports`` module provides functionality to assist with this.

Before we start our loop for receiving packets, we need to load in the
port information from the AX.25 subsystem, like this:

.. code-block:: python

   ports = ax25.ports.PortInfo()
   ports.load()

Once this is done, looking up the port information for each received
frame is accomplished with a single call. For example:

.. code-block:: python

   data, addr = sock.recvfrom(1024)
   port = ports.find_by_ifname(addr[0]).portname

This port information can then be passed in to a modified version of our
``print_frame()`` function, and included in the summary line, perhaps as
the first item in the line, as Linux' own ``listen`` utility does.

Note that AX.25 port information is not available through mechanisms
such as KISS or AGWPE, so this only applies when using the native AX.25
stack directly. (While KISS and AGWPE do have a concept of a port
number, this is not the same as an AX.25 port, and is effectively a
sequence number assigned to a connection by a server such as Direwolf.)

Using Connected Mode (Linux only)
---------------------------------

Although the Python ``socket`` module defines the ``AF_AX25`` value for
the AX.25 address family, it does not actually provide the means for using
it. In particular, there is no way to construct an AX.25 address, and
therefore no way to bind to one, or connect to one.

The ``ax25.socket`` module provides variants of the standard Python
socket methods that accept (only) AX.25 addresses. In keeping with the
other modules in this package, addresses may be provided as strings (i.e.
callsigns) or as ``ax25.Address`` instances. Once a socket is established
using these methods, it can then be manipulated using the usual Python
``socket`` methods.

This means that we can write, for example, connected mode applications in
Python. While writing a complete socket-based application is beyond the
scope of this User Guide, a full example is provided with this package,
in the form of a GUI application along the lines of the Linux ``axcall``
utility that is included with Linux's AX.25 software. Here we will show
how the connection is established; the remaining functionality is the
same as for regular socket applications.

First, we must create a new AX.25 socket:

.. code-block:: python

   sock = ax25.socket.Socket()

This socket is a subclass of the regular Python ``socket`` class, with
address family ``AF_AX25`` and, by default, a type of ``SOCK_SEQPACKET``,
which is what we want for connected mode use.

Now we need to create the connection between ourselves (source callsign)
and our target system (destination callsign). First we bind the socket.

.. code-block:: python

   def connect(sock, src_call, dst_call):
       sock.bind(src_call)

The code for working with the socket is a little more straightforward if
we use a non-blocking socket, so we need to set that up, since it would
be blocking by default.

.. code-block:: python

       sock.setblocking(False)

Now we can go ahead and request that a connection be made.

.. code-block:: python

       res = sock.connect_ex(dst_call)

This call will return immediately. To wait for the connection to complete,
or to timeout, we need to use a selector to wait until the socket is writable.

.. code-block:: python

       if res == errno.EINPROGRESS:
           with selectors.DefaultSelector() as sel:
               sel.register(self._sock, selectors.EVENT_WRITE)
               events = sel.select(self._CON_TIMEOUT)
               if not events:
                   log.error("Connection attempt has timed out")
                   return False
       elif res != 0:
           log.error("Connection attempt has failed")
           return False
       log.info("Connection created")
       return True

Note that we have simply logged a timeout or an error here. In reality,
you would want to notify the user appropriately.

This completes the code required to create a connected mode socket. Let's
take a look at the finished function:

.. code-block:: python

   def connect(sock, src_call, dst_call):
       sock.bind(src_call)
       sock.setblocking(False)
       res = sock.connect_ex(dst_call)
       if res == errno.EINPROGRESS:
           with selectors.DefaultSelector() as sel:
               sel.register(self._sock, selectors.EVENT_WRITE)
               events = sel.select(self._CON_TIMEOUT)
               if not events:
                   log.error("Connection attempt has timed out")
                   return False
       elif res != 0:
           log.error("Connection attempt has failed")
           return False
       log.info("Connection created")
       return True

That's it. Once the connection has been created, we can use regular Python
socket calls to work with this connection, sending and receiving data as
usual.

For a complete working example of how a connected mode socket is created
and used in a real-world working example, see the ``Connect`` example
provided with this package.
