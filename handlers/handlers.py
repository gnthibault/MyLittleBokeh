# coding=utf-8
from collections import defaultdict
from datetime import datetime
from random import randint
import random

import bokeh

# The bokeh figure
#from bokeh.models import ColumnDataSource, Slider
#from bokeh.plotting import figure
#from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

from bokeh.application.handlers import FunctionHandler
from bokeh.document import Document
from bokeh.embed import server_document
from bokeh.layouts import column

from bokeh.models import ColumnDataSource, Button, TableColumn, DateFormatter, DataTable


import tornado.web

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

def bokeh_app_old(doc):
    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(x_axis_type='datetime',
                  y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1,
                    title="Smoothing by N Days")
    slider.on_change('value', callback)
    doc.add_root(column(slider, plot))
    #doc.theme = Theme(filename="theme.yaml")

def bokeh_app(doc):
        source = ColumnDataSource(dict(x=[], y=[]))

        columns = [
            TableColumn(field="x", title="X"),
            TableColumn(field="y", title="Y"),
        ]

        data_table = DataTable(source=source, columns=columns)
        user_str = doc.session_context.id
        print(f"BOKEH APP STR IS {user_str}")
        doc_by_user_str[user_str] = doc
        source_by_user_str[user_str] = source
        
        doc.add_root(bokeh.models.Column(data_table))

class MainHandler(BaseHandler):
#    def modify_document(self, doc):
#        print("MODIFY DOCUMENT")
#        source = ColumnDataSource(dict(x=[], y=[]))
#
#        columns = [
#            TableColumn(field="x", title="X"),
#            TableColumn(field="y", title="Y"),
#        ]
#
#        data_table = DataTable(source=source, columns=columns)
#
#        user_str = doc.session_context.id
#        doc_by_user_str[user_str] = doc
#        source_by_user_str[user_str] = source
#        
#        doc.add_root(bokeh.models.Column(data_table))
#
#    _bokeh_app = None

#    @classmethod
#    def get_bokeh_app(cls):
#        if cls._bokeh_app is None:
#            cls._bokeh_app = bokeh.application.Application(FunctionHandler(MainHandler.modify_doc))
#        return cls._bokeh_app

    #@gen.coroutine
    @tornado.web.authenticated
    def get(self):
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"MAIN HANDLER THE STRING IS {self.current_user}")
        print(f"MAIN HANDLER {self.get_cookie('user')}")
        #script = server_session(model=None, session_id=user_str,
        #                        url='http://localhost:5006/bokeh/app')
        #script = server_document(url='http://localhost:5006/bokeh/app')

        #self.render(
        #        'main_page_template.html', active_page='inks_upload',
        #        script=script
        #)
        script = server_document('http://localhost:5006/bokeh_app')
        self.render(
                'main_page_template.html',
                script=script
        )

class SecondHandler(BaseHandler):
    def get(self):
        self.render("second_page_template.html")

    #@gen.coroutine
    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        user_str = tornado.escape.xhtml_escape(self.current_user)
        print(f"SecondHandler str {user_str}")

        data['x'] = random.sample(range(10), 10)
        data['y'] = random.sample(range(10), 10)

        data_by_user[user_str] = data
        source = source_by_user_str[user_str]
        #@gen.coroutine
        def update():
            source.data = data
        doc = doc_by_user_str[user_str]  # type: Document
        doc.add_next_tick_callback(update)  
        self.render('second_page_template.html')
