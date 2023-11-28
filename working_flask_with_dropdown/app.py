from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px

app = Flask(__name__)

@app.route('/compare', methods=['POST', 'GET'])
def compre():
    return generate_compare_graph(request.args.get('data'))
   
@app.route('/')
def index():
    return render_template('chartsajax.html')#,  graphJSON=gm())

def generate_compare_graph(country='United Kingdom'):
    df = pd.DataFrame(px.data.gapminder())

    fig = px.line(df[df['country']==country], x="year", y="gdpPercap", title=country)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

app.run()