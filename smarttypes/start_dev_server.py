
from multiprocessing import Process
from wsgiref.simple_server import make_server, WSGIRequestHandler
import time
import sys

class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        "if not overwritten, will print every page request"
        
def start_app():
    from smarttypes.wsgi import application
    port = 8282
    httpd = make_server('localhost', port, application,handler_class=CustomRequestHandler)
    print "Serving on port %s..." % port
    httpd.serve_forever()

def new_process():
    p = Process(target=start_app)
    p.start()
    return p

p = new_process()
while True:
    if p.exitcode:
        p = new_process()
    time.sleep(2.0)