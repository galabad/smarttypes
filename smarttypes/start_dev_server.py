

from wsgiref.simple_server import make_server, WSGIRequestHandler
from smarttypes.wsgi import application

class CustomRequestHandler(WSGIRequestHandler):
    
    def log_message(self, format, *args):
        ""
    
    #def handle(self):
        #"""Handle a single HTTP request"""

        #self.raw_requestline = self.rfile.readline()
        #if not self.parse_request(): # An error code has been sent, just exit
            #return

        #handler = ServerHandler(
            #self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        #)
        #handler.request_handler = self      # backpointer for logging
        #handler.run(self.server.get_app())


port = 8282
httpd = make_server('localhost', port, application,handler_class=CustomRequestHandler)
print "Serving on port %s..." % port
httpd.serve_forever()

