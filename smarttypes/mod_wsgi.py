
#need to hard code this stuff if using apache + mod_wsgi
import sys, site
sys.path.insert(0, "/home/timmyt/projects/smarttypes")
site.addsitedir("/home/timmyt/.virtualenvs/smarttypes/lib/python2.6/site-packages")

from smarttypes import config
config.CALLBACK = "http://www.smarttypes.org/my_account"
from smarttypes import wsgi
application = wsgi.application