# coding=utf-8
from collections import defaultdict
from datetime import datetime

# web stuff
import tornado
import bokeh
from bokeh.models import ColumnDataSource, TableColumn, DateFormatter, DataTable, NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool



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
    # Setup source for data
    source = ColumnDataSource(dict(x=[], y=[]))
    columns = [
        TableColumn(field="x", title="X"),
        TableColumn(field="y", title="Y"),
    ]
    data_table = DataTable(source=source, columns=columns)
    user_str = doc.session_context.id
    doc_by_user_str[user_str] = doc
    source_by_user_str[user_str] = source
    
    # Now setup nice plot
    #Graph configuration
    p = figure(title="Title", title_location='above',
               sizing_mode="scale_width", plot_width=800, plot_height=500)
    #Add Y Grid line - Set color to none
    p.ygrid.grid_line_color = None
    #Add X axis label
    p.xaxis.axis_label = "Date"
    #Add Y axis Label
    p.yaxis.axis_label = "Value"
    #Set Title configuration
    p.title.text_color = "black"
    p.title.text_font = "times"
    p.title.text_font_style = "italic"
    #Set background configuration
    p.background_fill_color = "white"
    p.background_fill_alpha = 0.5
    #Change X axis orientation label
    #p.xaxis.major_label_orientation = 1.2
    #------------Hover configuration -----------------#
    TOOLTIPS = [
        ("Date", "($x{0,0.00})"),
        ("Value", "($y{0,0.00})"),
    ]
    # Add the HoverTool to the figure for showing spectrum values
    p.add_tools(HoverTool(tooltips=TOOLTIPS, mode='vline'))
    # Plot actual data
    p.line('x', 'y',  source=source, legend_label='My variable of interest')
    #Set legen configuration (position and show/hide)
    p.legend.location = "top_left"
    p.legend.click_policy="hide"

    # Add to the doc
    #doc.add_root(bokeh.models.Column(data_table))
    doc.add_root(p)

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
        data['x'] = [datetime.now()]
        data['y'] = [np.random.rand()]

        data_by_user[user_str] = data
        source = source_by_user_str[user_str]
        @tornado.gen.coroutine
        def update():
            source.stream(data, rollover=32)
        doc = doc_by_user_str[user_str]  # type: Document
        doc.add_next_tick_callback(update)  
        self.render('second_page_template.html')
