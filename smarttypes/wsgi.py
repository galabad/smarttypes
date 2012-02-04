
import smarttypes
from smarttypes.utils import email_utils
import re, traceback
from webob import Request
from smarttypes.utils.web_response import WebResponse
from smarttypes.utils.exceptions import RedirectException
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.twitter_session import TwitterSession

urls = [
    (r'^$', smarttypes.controllers.index),
    
    (r'^sign_in/?$', smarttypes.controllers.sign_in),
    (r'^my_account/?$', smarttypes.controllers.my_account),
    (r'^save_email/?$', smarttypes.controllers.save_email),
    
    (r'^blog/?', smarttypes.controllers.blog),
    
    (r'^social_map/?$', smarttypes.controllers.social_map.index),
    (r'^social_map/map_data.json', smarttypes.controllers.social_map.map_data),
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
                postgres_handle = PostgresHandle(smarttypes.connection_string)
                try:
                    session = None
                    if request.cookies.get('session'):
                        session = TwitterSession.get_by_request_key(request.cookies['session'], postgres_handle)
                    response_dict = controller(request, session, postgres_handle)
                    web_response = WebResponse(request, controller.__name__, response_dict, session)
                    response_headers = web_response.get_response_headers()
                    response_string = web_response.get_response_str()
                    if getattr(postgres_handle, '_connection', False):
                        postgres_handle.connection.commit()
                    status_code = '200 OK'
                except RedirectException, (redirect_ex):                
                    if getattr(postgres_handle, '_connection', False):
                        postgres_handle.connection.commit()
                    status_code = '303 See Other'
                    response_headers = [('Location', redirect_ex.redirect_url)]
                    response_string = [""]
                except:
                    if getattr(postgres_handle, '_connection', False):
                        postgres_handle.connection.rollback()
                    raise
                finally:
                    if getattr(postgres_handle, '_connection', False):
                        postgres_handle.connection.close()                 
                
                #start response
                start_response(status_code, response_headers)
                return response_string
            
            except Exception, ex:
                #can't use print statements with mod_wsgi
                error_string = traceback.format_exc()
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                email_utils.send_email('error@smarttypes.org', ['timmyt@smarttypes.org'], 
                                       error_string, 'smarttypes site error')
                return [error_string]
        
    #couldn't find it        
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return ["Couldn't find the URL specified. %s" % path]