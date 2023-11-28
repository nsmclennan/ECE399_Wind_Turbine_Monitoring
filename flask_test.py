from flask import Flask, request, abort, render_template

from datetime import datetime, timezone
from struct import unpack_from
import numpy as np
import pandas as pd
import plotly.express as px
import plotly
import json
# Simulate Data

# Flask Implementation
app = Flask(__name__)

@app.post("/upload/<int:freq>")
@app.post("/upload/<int:freq>/<end_time>")
def upload(freq, end_time=None):
    if end_time is None:
        end_time = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    try:
        end_time = datetime.strptime(end_time, "%Y%m%d%H%M%S")
    except ValueError:
        app.logger.warning("Invalid datetime string")
        abort(400)
    
    if request.content_length > 3e5:
        app.logger.warning("Content length exceeds limit")
        abort(400)
    if request.content_length % 12 != 0:
        app.logger.warning("Invalid content format")
        abort(400)
    
    app.logger.debug(f"Upload received ({freq} Hz, {end_time.replace(tzinfo=timezone.utc).astimezone(tz=None)})")
    
    raw_data = request.data
    # Store most recent data 10 second chunk
    # Store to a file or sqlite unparsed
    with open("data/sample_" + str(freq) + ".raw", "wb") as file:
        file.write(raw_data)

    # TODO save raw (or parsed) data
    df = parse_data(freq)
    print(df)
    
    return '', 200

def parse_data(freq):
    # TODO avg for each column?
    with open("data/sample_" + str(freq) + ".raw", "rb") as file:
        raw_data = file.read()

    
    data = []
    for i in range(len(raw_data)//12):
        gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z = unpack_from("<hhhhhh", raw_data, i*12)
        
        accel_mag = (accel_x**2 + accel_y**2 + accel_z**2)**0.5
        t = i/int(freq)
        
        # Convert raw values to nice units
        gf = 2000*2/65536 # LSB in 2000 deg/s mode
        gf *= np.pi / 180 # Convert degrees to radians
        af = 1/16384 # 2*2/65536 # LSB/g in 2g mode
        
        data.append([gf*gyro_x, gf*gyro_y, gf*gyro_z, af*accel_x, af*accel_y, af*accel_z, af*accel_mag, t])
    
    #return data
    return pd.DataFrame(data, columns=["Gyro X [rad/s]", "Gyro Y [rad/s]", "Gyro Z [rad/s]", "Accel X [g]", "Accel Y [g]", "Accel Z [g]", "Accel Mag [g]", "Time [s]"])

@app.route('/callback', methods=['POST', 'GET'])
def cb():
    return gm(request.args.get('data'))

# Render main template
@app.route("/")
def main_page():
    return render_template("home.html")


def gm(freq='1600'):
    df = parse_data(freq)

    fig = px.line(df, x=df.columns[-1], y=df.columns[0:-1], title="Time Domain")

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


# Run flask
app.run()

# Get sqlite working
# gyro, accel graph