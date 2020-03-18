# coding=utf-8
import os.path

import bokeh
import tornado
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import Server
from bokeh.util.browser import view
from tornado.options import define, options

from handlers.handlers import MainHandler, LoginHandler, SecondHandler

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/login", LoginHandler),
            (r"/main_page", MainHandler),
            (r"/second_page", SecondHandler),
        ]
        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                xsrf_cookies=True,
                # NOTE: some random value as secret (i.e. generated by uuid4())
                cookie_secret="YOUR SECRET HERE",
                login_url="/login",
                debug=True,
        )
        super(Application, self).__init__(handlers, **settings)



if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    io_loop = tornado.ioloop.IOLoop.current()

    bokeh_app = bokeh.application.Application(FunctionHandler(MainHandler.modify_doc))

    bokeh_server = Server({'/bokeh/app': bokeh_app},
                          io_loop=io_loop, allow_websocket_origin=['localhost:8888'])
    bokeh_server.start()

    io_loop.add_callback(view, "http://localhost:8888/main_page")
    io_loop.start()
