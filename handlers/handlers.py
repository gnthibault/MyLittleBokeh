# coding=utf-8
from collections import defaultdict
from datetime import datetime
from random import randint
import random

# web stuff
import tornado
import bokeh
from bokeh.models import ColumnDataSource, Button, TableColumn, DateFormatter, DataTable

# Numerical stuff
import numpy as np

data_by_user = defaultdict(lambda: dict(file_names=[], dates=[], downloads=[]))
doc_by_user_str = dict()
source_by_user_str = dict()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class LoginHandler(BaseHandler):
    def get(self):
        self.render(
                'login_template.html',
        )

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")


def bokeh_app(doc):
    source = ColumnDataSource(dict(x=[], y=[]))

    columns = [
        TableColumn(field="x", title="X"),
        TableColumn(field="y", title="Y"),
    ]

    data_table = DataTable(source=source, columns=columns)
    user_str = doc.session_context.id
    doc_by_user_str[user_str] = doc
    source_by_user_str[user_str] = source
    
    doc.add_root(bokeh.models.Column(data_table))

class MainHandler(BaseHandler):

    @tornado.gen.coroutine
    @tornado.web.authenticated
    def get(self):
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"MAIN HANDLER THE STRING IS {self.current_user}")
        print(f"MAIN HANDLER {self.get_cookie('user')}")
        script = bokeh.embed.server_session(session_id=user_str,
            url='http://localhost:5006/bokeh_app')
        self.render(
                'main_page_template.html',
                script=script
        )

class SecondHandler(BaseHandler):
    def get(self):
        self.render("second_page_template.html")

    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"SecondHandler str {user_str}")

        data = {}
        data['x'] = [np.random.rand()]
        data['y'] = [np.random.rand()]

        data_by_user[user_str] = data
        source = source_by_user_str[user_str]
        @tornado.gen.coroutine
        def update():
            source.stream(data, rollover=16384)
        doc = doc_by_user_str[user_str]  # type: Document
        doc.add_next_tick_callback(update)  
        self.render('second_page_template.html')
