
import smarttypes
import re, traceback
from webob import Request

urls = [
    (r'^$', smarttypes.controllers.index),
    
    (r'^sign_in/?$', smarttypes.controllers.sign_in),
    (r'^my_account/?$', smarttypes.controllers.my_account),
    (r'^save_email/?$', smarttypes.controllers.save_email),
    
    (r'^blog/?', smarttypes.controllers.blog),
    
    (r'^social_map/?$', smarttypes.controllers.social_map.index),
    (r'^social_map/map_data.json$', smarttypes.controllers.social_map.map_data),
    (r'^social_map/ajax_group/?$', smarttypes.controllers.social_map.ajax_group),
    
    (r'^contact/?$', smarttypes.controllers.contact),
    
    (r'^static/?', smarttypes.controllers.static),
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