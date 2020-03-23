import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from testandtrade.dataloader import dataloader
import webbrowser
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import flask
from gevent.pywsgi import WSGIServer
import logging
import socket


def Launch(stratName, data=[], labels=[], dates=None):

    server = flask.Flask(__name__)
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, server, external_stylesheets=external_stylesheets)

    dropOps = []
    for x in range(0,len(labels)):
        dropOps.append({"label":labels[x],"value":x})


    app.layout = html.Div([html.H1(stratName, style={'textAlign': 'center'}),
        dcc.Dropdown(id='my-dropdown',options=dropOps,
            multi=True,value=[0],style={"display": "block","margin-left": "auto","margin-right": "auto","width": "60%"}),
        dcc.Graph(id='my-graph')
        ], className="container")


    @app.callback(Output('my-graph', 'figure'),
                  [Input('my-dropdown', 'value')])
    def update_graph(selected_dropdown_value,data=data,dates=dates,labels=labels):
        dropdown = {"TSLA": "Tesla","AAPL": "Apple","COKE": "Coke",}
        trace1 = []
        trace2 = []
        for value in selected_dropdown_value:
            trace1.append(go.Scatter(x=dates,y=data[value],mode='lines',
                opacity=0.7,name=labels[value],textposition='bottom center'))
        traces = [trace1]
        data = [val for sublist in traces for val in sublist]
        figure = {'data': data,
            'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                height=600,
                xaxis={"title":"Date",
                       'rangeslider': {'visible': True}, 'type': 'date'},
                       yaxis={"title":"Price (USD)"})}
        return figure


    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.logger.disabled = True

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    x = s.getsockname()[1]
    http_server = WSGIServer(('', x), server, log=None)
    webbrowser.open_new("http://localhost:"+str(x)+"/")
    logging.disable(logging.CRITICAL)
    print("Loading plots in browser")
    http_server.serve_forever()
