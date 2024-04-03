# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import ax25


# -- Project information -----------------------------------------------------

project = 'PyHam AX.25'
copyright = '2024, Martin F N Cooper. All rights reserved'
author = 'Martin F N Cooper'
release = ax25.__version__
version = release


# -- General configuration ---------------------------------------------------

extensions = [
    'autoapi.extension'
]
autoapi_dirs = ['../ax25']
autoapi_options = [
    'members',
    'show-inheritance',
    'show-module-summary',
    'imported-members'
]

templates_path = ['_templates']

rst_prolog = """
.. meta::
   :author: Martin F N Cooper
   :description: A set of Python modules for working with AX.25 packets in an
      amateur packet radio environment.
"""


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'prev_next_buttons_location': 'none'
}
html_show_sourcelink = False
