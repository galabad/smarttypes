import os
import smarttypes
from smarttypes.model.twitter_signup import TwitterSession
import webob
from genshi.core import Stream
from genshi.output import encode, get_serializer
from genshi.template import Context, TemplateLoader    

#template loader
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), '../templates'),
    auto_reload=True)


class WebResponse(object):
    
    def __init__(self, req, controller_name, response_dict, credentials):
        self.req = req
        self.controller_name = controller_name
        self.response_dict = response_dict
        self.return_str = response_dict.get('return_str')
        self.content_type = response_dict.get('content_type', 'text/html')
        self.cookies = response_dict.get('cookies', [])
        self.webob_response = webob.Response()
        self.credentials = credentials or response_dict.get('credentials')
                
    def get_response_headers(self):
        if self.content_type == 'text/json':
            raise Exception('TODO: need to hook up simple json.')
        headers = [('Content-Type', '%s; charset=utf-8' % self.content_type)]
        for key, value in self.cookies:
            self.webob_response.set_cookie(key, value, 31*24*60*60)
            headers.append(('Set-Cookie', self.webob_response.headers['Set-Cookie']))
        return headers

    def get_response_str(self):
        #if there's a string we'll just return that
        if self.return_str:
            return [self.return_str]
        
        #global
        self.response_dict['site_name'] = smarttypes.site_name
        self.response_dict['site_mantra'] = smarttypes.site_mantra 
        self.response_dict['site_description'] = smarttypes.site_description
        
        #defaults
        if not 'title' in self.response_dict: 
            self.response_dict['title'] = smarttypes.default_title
        if not 'template_path' in self.response_dict: 
            self.response_dict['template_path'] = '%s.html' % self.controller_name
        if not 'active_tab' in self.response_dict: 
            self.response_dict['active_tab'] = self.controller_name
                
        #session
        self.response_dict['logged_in_credentials'] = None
        self.response_dict['logged_in_user'] = None
        if self.credentials:
            self.response_dict['logged_in_credentials'] = self.credentials
            self.response_dict['logged_in_user'] = self.credentials.twitter_user
            
        template = loader.load(self.response_dict['template_path'])
        template_with_dict = template.generate(**self.response_dict)
        response_str = template_with_dict.render(self.content_type.split('/')[1])
        
        return [response_str]
    
    
    
    
    
    
    
    

