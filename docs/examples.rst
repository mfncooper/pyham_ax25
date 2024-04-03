.. _examples:

Examples
========

Included with this package are some complete example applications that
illustrate how the library can be used to build real world software.

Listen
------

A command line application that enables monitoring of AX.25 frames in a manner
similar to that of the ``listen`` utility available on Linux.

Frames are decoded using the ``ax25`` module, and embedded NET/ROM broadcast
data is decoded using the ``ax25.netrom`` module. When running under Linux and
on top of the Linux AX.25 protocol stack, the ``ax25.ports`` module is used
to identify the incoming port. (Port information is not available via KISS.)

The application supports two different means of acquiring AX.25 packets. On
all platforms, it can connect to software such as Direwolf using KISS, and
receive packets provided to it through that connection. On Linux only, it can
use the native AX.25 protocol stack to receive packets directly.

**Note:** In order to avoid any package dependencies, the KISS code uses a
very simplistic method for extracting the data from a KISS frame. This is
not foolproof. If you wish to create a more robust version of this example,
see the ``pyham_kiss`` package.

Connect
-------

.. important::
   The `Connect` application runs only on Linux, since it illustrates the use
   of the ``ax25.socket`` module in working with the native Linux AX.25 stack.

A command line application along the lines of the Linux ``axcall`` utility,
providing simple connected mode capability and demonstrating the use of the
``ax25.socket`` module.

Few commands and options are provided, since the focus is on illustrating the
ease with which a simple connected mode application can be constructed on top
of the native Linux AX.25 stack using ``ax25.socket``. In particular, only the
default port is supported in this example application, and vias are not
supported. These are both supported by the ``ax25.socket`` module, however, and
would be straightforward to add should someone choose to use this example as
the basis for a more sophisticated application.
