from flask import Flask, request, abort

from datetime import datetime, timezone
from struct import unpack_from
import numpy as np
import pandas as pd


app = Flask(__name__)


@app.route("/")
def index():
    return "<p>Hello, World!</p>"

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
    # TODO save raw (or parsed) data
    df = parse_data(raw_data, freq)
    print(df)
    
    return '', 200

def parse_data(raw_data, freq):
    # TODO avg for each column?
    data = []
    for i in range(len(raw_data)//12):
        gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z = unpack_from("<hhhhhh", raw_data, i*12)
        
        accel_mag = (accel_x**2 + accel_y**2 + accel_z**2)**0.5
        t = i/freq
        
        # Convert raw values to nice units
        gf = 2000*2/65536 # LSB in 2000 deg/s mode
        gf *= np.pi / 180 # Convert degrees to radians
        af = 1/16384 # 2*2/65536 # LSB/g in 2g mode
        
        data.append([gf*gyro_x, gf*gyro_y, gf*gyro_z, af*accel_x, af*accel_y, af*accel_z, af*accel_mag, t])
    
    #return data
    return pd.DataFrame(data, columns=["Gyro X [rad/s]", "Gyro Y [rad/s]", "Gyro Z [rad/s]", "Accel X [g]", "Accel Y [g]", "Accel Z [g]", "Accel Mag [g]", "Time [s]"])

if __name__ == "__main__":
    app.run(debug=True, use_evalex=False)
    #flask --app receiver_test_simple run --debug --no-debugger
