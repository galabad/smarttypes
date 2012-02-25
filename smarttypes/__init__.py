"""
====================
Modules
====================

Modules are stored in a global dict, and loaded from the top down.

Module (x) may load another module (y)

If y then loads x (a cross-reference) it will only have the
parts of x that were loaded when itself (y) was called by x



====================
This app
====================

mod_wsgi loads wsgi.py

wsgi.py imports this, which should import everything else
"""

import utils  # need this
import model  # need this
import controllers  # need this
from config import DB_USER, DB_PASSWORD
connection_string = "host=localhost dbname='smarttypes' user='%s' password='%s'" % (DB_USER, DB_PASSWORD)

site_name = 'SmartTypes'
site_mantra = 'a tool for social discovery'
default_title = '%s - %s' % (site_name, site_mantra)
site_description = """
SmartTypes is an open platform for social network exploration.
Our software is free and available on github.
Our aim is to model and understand the complex interactions and interests of niche social groups.
Our methods are influenced by biological, physical, and complexity science.
Sign in w/ your twitter account to reserve a spot on our free beta roster.
"""
site_description = site_description.strip()
