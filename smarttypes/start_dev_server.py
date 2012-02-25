utils = __import__('utils')
model = __import__('model')
from multiprocessing import Process
from wsgiref.simple_server import make_server, WSGIRequestHandler
import time
import os


class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        "if not overwritten, will print every page request"


def start_app():
    from wsgi import application
    from smarttypes.utils import web_monitor
    web_monitor.start(interval=1.0)
    project_path = os.path.dirname(os.path.abspath(__file__))
    web_monitor.track(project_path + '/templates/')
    port = 8282
    httpd = make_server('localhost', port, application, handler_class=CustomRequestHandler)
    print "Serving on port %s..." % port
    httpd.serve_forever()


def new_process():
    p = Process(target=start_app)
    p.start()
    return p

if __name__ == '__main__':
    p = new_process()
    while True:
        if p.exitcode:
            p = new_process()
        time.sleep(2.0)
