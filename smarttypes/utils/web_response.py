import os
# import smarttypes
from model.twitter_session import TwitterSession
import webob
from genshi.core import Stream
from genshi.output import encode, get_serializer
from genshi.template import Context, TemplateLoader
import simplejson

#template loader
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), '../templates'),
    auto_reload=True)


class WebResponse(object):

    def __init__(self, req, controller_name, response_dict, session):
        self.req = req
        self.controller_name = controller_name
        self.response_dict = response_dict
        self.return_str = response_dict.get('return_str')
        #self.content_type = response_dict.get('content_type', 'text/html')

        #Note that you'll have to detect Internet Explorer (and other browsers that don't understand XHTML)
        #on the server and change the content type to text/html - if presented with the application/xhtml+xml
        #content type IE will prompt the user to download the file;
        #self.content_type = response_dict.get('content_type', 'application/xhtml+xml')
        self.content_type = response_dict.get('content_type', 'text/html')
        self.cookies = response_dict.get('cookies', [])
        self.webob_response = webob.Response()
        self.session = response_dict.get('session') or session

    def get_response_headers(self):
        if self.content_type == 'application/json':
            if not self.return_str:
                self.return_str = simplejson.dumps(self.response_dict['json'])
        headers = [('Content-Type', '%s; charset=utf-8' % self.content_type)]
        for key, value in self.cookies:
            self.webob_response.set_cookie(key, value, 31 * 24 * 60 * 60)
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
        if not 'meta_page_description' in self.response_dict:
            self.response_dict['meta_page_description'] = smarttypes.site_description
        if not 'template_path' in self.response_dict:
            self.response_dict['template_path'] = '%s.html' % self.controller_name
        if not 'active_tab' in self.response_dict:
            self.response_dict['active_tab'] = self.controller_name

        #session stuff
        if not 'session' in self.response_dict:
            self.response_dict['session'] = self.session
        self.response_dict['credentials'] = None
        if self.response_dict['session'] and self.response_dict['session'].credentials:
            self.response_dict['credentials'] = self.response_dict['session'].credentials
        self.response_dict['logged_in_user'] = None
        if self.response_dict['credentials'] and self.response_dict['credentials'].twitter_user:
            self.response_dict['logged_in_user'] = self.response_dict['credentials'].twitter_user

        template = loader.load(self.response_dict['template_path'])
        template_with_dict = template.generate(**self.response_dict)
        response_str = template_with_dict.render(self.content_type.split('/')[1])
        #response_str = template_with_dict.render('xhtml')

        return [response_str]
