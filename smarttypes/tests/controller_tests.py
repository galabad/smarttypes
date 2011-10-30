import smarttypes
from smarttypes.wsgi import application
from webob import Request

def test_urls():

    def test_url(url):
        req = Request.blank(url)
        response = req.get_response(application)
        if not response.body.find('<!--end footer-->') > -1:
            print response.body
            raise Exception("Could not find '<!--end footer-->' in response body.")
        
    #home page
    test_url('/')
    test_url('/about')
    
    test_url('/projects/farmbucket')
    test_url('/projects/garden_vitals')
    
    test_url('/essays/the_unforeseen') 
    test_url('/essays/we_are_the_past') 
    
if __name__ == '__main__':
    test_urls()