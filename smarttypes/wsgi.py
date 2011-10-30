
import smarttypes
import re, traceback
from webob import Request

from smarttypes.utils import web_monitor
web_monitor.start(interval=1.0)
web_monitor.track('/home/timmyt/projects/smarttypes/smarttypes/templates')

urls = [
    (r'^$', smarttypes.controllers.home),
    
    (r'sign_in/?$', smarttypes.controllers.sign_in),
    (r'my_account/?$', smarttypes.controllers.my_account),
    (r'save_email/?$', smarttypes.controllers.save_email),
    
    (r'user/?$', smarttypes.controllers.user),
    (r'group/?$', smarttypes.controllers.group),    
    
    (r'blog/?', smarttypes.controllers.blog),
    
    (r'about/?$', smarttypes.controllers.about),
    (r'contact/?$', smarttypes.controllers.contact),
    
    (r'static/?', smarttypes.controllers.static),
]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, controller in urls:
        match = re.search(regex, path)
        if match:
            request = Request(environ)
            try:
                status_code, response_headers, body = controller(request)
                start_response(status_code, response_headers)
                return body
            except Exception, ex:
                #can't use print statements with mod_wsgi
                error_string = traceback.format_exc()
                start_response('500 Internal Server Error', 
                               [('Content-Type', 'text/plain')])
                return [error_string]
        
    #couldn't find it        
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return ["Couldn't find the URL specified. %s" % path]