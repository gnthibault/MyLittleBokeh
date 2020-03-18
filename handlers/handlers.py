# coding=utf-8
from collections import defaultdict
from datetime import datetime
from random import randint
import random

import bokeh
import bokeh.application as bokeh_app

from bokeh.application.handlers import FunctionHandler
from bokeh.document import Document
from bokeh.embed import server_document
from bokeh.layouts import column

from bokeh.models import ColumnDataSource, Button, TableColumn, DateFormatter, DataTable
#from bokeh.plotting import figure, output_file, show






import tornado.web
# authenticate decorator is = if not self.current_user: self.redirect()
from tornado.web import authenticated

data_by_user = defaultdict(lambda: dict(file_names=[], dates=[], downloads=[]))
doc_by_user_str = dict()
source_by_user_str = dict()

data = dict(x=[], y=[])

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

class MainHandler(BaseHandler):
    def modify_document(self, doc):
        print("MODIFY DOCUMENT")
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

    _bokeh_app = None

    @classmethod
    def get_bokeh_app(cls):
        if cls._bokeh_app is None:
            cls._bokeh_app = bokeh.application.Application(FunctionHandler(MainHandler.modify_doc))
        return cls._bokeh_app

    #@gen.coroutine
    @authenticated
    def get(self):
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"THE STRING IS {self.current_user}")
        #script = server_session(model=None, session_id=user_str,
        #                        url='http://localhost:5006/bokeh/app')
        script = server_document(url='http://localhost:5006/bokeh/app')

        self.render(
                'main_page_template.html', active_page='inks_upload',
                script=script
        )

class SecondHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("second_page_template.html")

    #@gen.coroutine
    @authenticated
    def post(self, *args, **kwargs):
        print(f"NOW IN SecondHandler !!!")
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"SecondHandler str {user_str}")

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
