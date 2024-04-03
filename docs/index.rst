PyHam AX.25
===========

Overview
--------

This package provides a set of modules for working with AX.25 packets in an
amateur packet radio environment. The package comprises two functionally
distinct components.

- The ``ax25`` and ``ax25.netrom`` modules provide structure definitions
  together with methods to pack and unpack native AX.25 frames and NET/ROM
  routing table updates. These modules work on all platforms, and can be used
  together with the transport mechanism(s) of your choice.

- The ``ax25.ports`` and ``ax25.socket`` modules provide facilities for working
  with the Linux native AX.25 stack. Unlike other Python AX.25 packages, this
  includes the creation and use of connected-mode sessions, and thus it is not
  limited to unproto (UI frame) usage.

This package does *not* include implementations of transport mechanisms such as
KISS or AGWPE. However, other PyHam packages do provide this, or you can use
this package in conjunction with any other such software of your choosing.

It is expected that developers working with this package will have some level
of knowledge of the AX.25 protocol. Those less familiar with the protocol may
wish to refer to the
`AX.25 protocol specification <http://www.tapr.org/pdf/AX25.2.2.pdf>`__
in conjunction with the documentation for this package.

:Author: Martin F N Cooper, KD6YAM
:License: :doc:`MIT License <license>`

Limitations
~~~~~~~~~~~

- The ``ax25`` module supports almost all of the AX.25 v2.2 protocol. The sole
  exception is that only modulo 8 control fields are supported; modulo 128
  control fields are not yet supported.

- The ``ax25.netrom`` module currently supports only routing broadcasts. That
  is, NET/ROM I-frame packets are not yet supported.

Installation
------------

.. important::
   This package requires Python 3.7 or later.

The PyHam AX.25 package is distributed on
`PyPI <https://pypi.org/project/pyham_ax25/>`__,
and should be installed with pip as follows:

.. code-block:: console

   $ pip install pyham_ax25

Then the modules you require may be imported with the appropriate subset of the
following:

.. code-block:: python

   import ax25
   import ax25.netrom
   import ax25.ports
   import ax25.socket

The source code is available from the
`GitHub repository <https://github.com/mfncooper/pyham_ax25>`__:

.. code-block:: console

   $ git clone https://github.com/mfncooper/pyham_ax25


Documentation
-------------

:doc:`userguide`
   The User Guide walks through some use cases for the package, starting from
   the basics and adding capability as it progresses.
:doc:`examples`
   Complete example applications are included, in order that a developer can
   observe the usage of the package in a real-world scenario.
:doc:`autoapi/index`
   If you are looking for information on a specific function, class, or method,
   this part of the documentation is for you.

References
----------

AX.25 v2.2 protocol reference:
  http://www.tapr.org/pdf/AX25.2.2.pdf

NET/ROM protocol reference:
  https://packet-radio.net/wp-content/uploads/2017/04/netrom1.pdf

About PyHam
-----------

PyHam is a collection of Python packages targeted at ham radio enthusiasts who
are also software developers. The name was born out of a need to find unique
names for these packages when the most obvious names were already taken.

PyHam packages aim to provide the kind of functionality that makes it much
simpler to build sophisticated ham radio applications without having to start
from scratch. In addition to the packages, PyHam aims to provide useful
real-world ham radio applications for all hams.

See the `PyHam home page <https://pyham.org>`__ for more information, and a
list of currently available libraries and applications.

.. toctree::
   :maxdepth: 2
   :hidden:

   Getting Started <self>
   userguide
   examples
   autoapi/index
   license
   genindex
