# coding=utf-8
from collections import defaultdict
from datetime import datetime
from random import randint
import random

import bokeh
import bokeh.application as bokeh_app
import tornado.web
from bokeh.application.handlers import FunctionHandler
from bokeh.document import Document
from bokeh.embed import server_session, server_document
from bokeh.layouts import column, widgetbox
from bokeh.models import ColumnDataSource, Button, TableColumn, DateFormatter, DataTable
from tornado import gen

data_by_user = defaultdict(lambda: dict(file_names=[], dates=[], downloads=[]))
doc_by_user_str = dict()
source_by_user_str = dict()

data = dict(x=[], y=[])

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")

class MainHandler(BaseHandler):
    @staticmethod
    def modify_doc(doc):
        source = ColumnDataSource(dict(x=[], y=[]))

        columns = [
            TableColumn(field="x", title="X"),
            TableColumn(field="y", title="Y"),
        ]

        data_table = DataTable(source=source, columns=columns)

        user_str = doc.session_context.id
        doc_by_user_str[user_str] = doc
        source_by_user_str[user_str] = source
        
        doc.add_root(widgetbox(data_table))

    _bokeh_app = None

    @classmethod
    def get_bokeh_app(cls):
        if cls._bokeh_app is None:
            cls._bokeh_app = bokeh.application.Application(FunctionHandler(MainHandler.modify_doc))
        return cls._bokeh_app

    @gen.coroutine
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        user_str = str(self.current_user)
        print(f"THE STRING IS {self.current_user}")
        script = server_session(model=None, session_id=user_str,  # NOTE: MUST be string
                                         url='http://localhost:5006')
       #                  app_path='/bokeh/app',

        self.render(
                'main_page_template.html', active_page='inks_upload',
                script=script
        )

class SecondHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("second_page_template.html")

    @gen.coroutine
    def post(self, *args, **kwargs):
        user_str = str(self.current_user)

        data['x'] = random.sample(range(10), 10)
        data['y'] = random.sample(range(10), 10)

        data_by_user[user_str] = data

        source = source_by_user_str[user_str]

        @gen.coroutine
        def update():
            source.data = data

        doc = doc_by_user_str[user_str]  # type: Document
        
        # Bryan Van de Ven @bryevdv Feb 27 22:23
        # @Sklavit actually I can see why next_tick_callback would be needed from another request handler. 
        # We had other threads in mind but it's also the case that nothing triggering your other request handler 
        # would acquire a bokeh document lock, so you need to request one by using next_tick_callback
        doc.add_next_tick_callback(update)  

        self.render('second_page_template.html')
