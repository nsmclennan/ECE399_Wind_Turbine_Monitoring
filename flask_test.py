from flask import Flask, request, abort, render_template

from datetime import datetime, timezone
from struct import unpack_from
import numpy as np
import pandas as pd
import plotly.express as px
import plotly
import json
import scipy.signal as signal
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
    with open("data/reference_sample_" + str(freq) + ".raw", "wb") as file:
        file.write(raw_data)

    # TODO save raw (or parsed) data
    df = parse_data(freq)
    
    return '', 200

def parse_data(freq, reference = False):
    # TODO avg for each column?
    # If new sample data
    if not reference:
        data_path = "data/sample_"
    else:
        data_path = "data/reference_sample_"

    with open(data_path + str(freq) + ".raw", "rb") as file:
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
    
    columns_index_names = ["Gyro X [rad/s]", "Gyro Y [rad/s]", "Gyro Z [rad/s]", "Accel X [g]", "Accel Y [g]", "Accel Z [g]", "Accel Mag [g]", "Time [s]"]
    #If new sample data
    if reference:
        columns_index_names = [x + " Reference" if "Time" not in x else x for x in columns_index_names]
    return pd.DataFrame(data, columns=columns_index_names)


@app.route('/time_graph', methods=['POST', 'GET'])
def time_graph():
    data = request.args.get('data')
    # Sometimes crashes on first load of the graph
    # https://community.plotly.com/t/valueerror-invalid-value-in-basedatatypes-py/55993/6
    try:
        graph_JSON = generate_time_json(data)
    except ValueError:
        graph_JSON = generate_time_json(data)
    return graph_JSON

@app.route('/fft_graph', methods=['POST', 'GET'])
def fft_graph():
    data = request.args.get('data')
    print(data)
    # Sometimes crashes on first load of the graph
    # https://community.plotly.com/t/valueerror-invalid-value-in-basedatatypes-py/55993/6
    try:
        graph_JSON = generate_fft_json(data)
    except ValueError:
        graph_JSON = generate_fft_json(data)
    return graph_JSON

@app.route('/psd_graph', methods=['POST', 'GET'])
def psd_graph():
    data = request.args.get('data')
    # Sometimes crashes on first load of the graph
    # https://community.plotly.com/t/valueerror-invalid-value-in-basedatatypes-py/55993/6
    try:
        graph_JSON = generate_psd_json(data)
    except ValueError:
        graph_JSON = generate_psd_json(data)
    return graph_JSON

@app.route('/compare_graph', methods=['POST', 'GET'])
def compare_graph():
    data = request.args.get('data')
    compare_value = request.args.get('compare_value')
    # Sometimes crashes on first load of the graph
    # https://community.plotly.com/t/valueerror-invalid-value-in-basedatatypes-py/55993/6
    try:
        graph_JSON = select_compare_graph(data, compare_value)
    except ValueError:
        graph_JSON = select_compare_graph(data, compare_value)
    return graph_JSON

# Render main template
@app.route("/")
def main_page():
    return render_template("home.html")

COMPARE_VALUE_TYPE_INDEX = 0
COMPARE_VALUE_AXIS_INDEX = 1
DF_COLUMN_NAME_MAX_LENGTH = 5

def select_compare_graph(freq = "1600", compare_value = "a_x_t"):
    graph_JSON = None
    if "_t" in compare_value: # Time domain analysis
        graph_JSON = generate_compare_time_graph(freq, compare_value)
    elif "_fft" in compare_value: # fft analysis
        graph_JSON = generate_compare_fft_graph(freq, compare_value)
    elif "_psd" in compare_value: # psd analysis
        graph_JSON = generate_compare_psd_graph(freq, compare_value)

    return graph_JSON

def generate_compare_time_graph(freq, compare_value):
    # Parse data
    df = parse_data(freq)
    # Parse reference data
    df_reference = parse_data(freq, reference = True)

    # Get column index for the corresponding compare_value
    column_name_index = None
    for col_index, col in enumerate(df.columns):
        if compare_value.split("_")[COMPARE_VALUE_TYPE_INDEX].upper() in col: # Get the a/g
            if compare_value.split("_")[COMPARE_VALUE_AXIS_INDEX].upper() in col: # Get the x/y/z
                column_name_index = col_index # Get the index to pull from df

    # TODO Open saved data file and display it with the current sample values

    fig = px.line(pd.concat([df, df_reference]), x=df.columns[-1], y=[df.columns[column_name_index],df_reference.columns[column_name_index]], title="Time Domain")

    graph_JSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON

def generate_compare_fft_graph(freq, compare_value):
    fs = int(freq)
    # Parse data
    df = parse_data(freq)
    df_reference = parse_data(freq, reference = True)
    # Get column index for the corresponding compare_value
    column_name_index = None
    for col_index, col in enumerate(df.columns):
        if compare_value.split("_")[COMPARE_VALUE_TYPE_INDEX].upper() in col: # Get the a/g
            if compare_value.split("_")[COMPARE_VALUE_AXIS_INDEX].upper() in col: # Get the x/y/z
                column_name_index = col_index # Get the index to pull from df

    # TODO Open saved data file and display it with the current sample values

    # Generate graph with selected name
    data = df.to_numpy()
    data_reference = df_reference.to_numpy()
    

    fft_data = np.transpose(np.fft.rfft(data[:, :-1], axis=0, norm="forward")) # Display traces for all params (normalized by length)
    fft_data = np.abs(fft_data) # Magnitude

    fft_data_reference = np.transpose(np.fft.rfft(data_reference[:, :-1], axis=0, norm="forward")) # Display traces for all params (normalized by length)
    fft_data_reference = np.abs(fft_data_reference) # Magnitude

    # Double non-DC components to account for neg frequencies
    fft_data[:, 1:] *= 2
    fft_data_reference[:, 1:] *= 2

    fft_x = np.fft.rfftfreq(len(data), 1/fs)

    # Skip DC point - MAKES GRAPH READABLE MAY NOT BE VALID
    fft_x = fft_x[1:]
    fft_data = fft_data[:, 1:]
    fft_data_reference = fft_data_reference[:, 1:]
    
    fft_df = pd.DataFrame({df.columns[i]: fft_data[i] for i in range(len(fft_data))})
    fft_df_reference = pd.DataFrame({df_reference.columns[i]: fft_data_reference[i] for i in range(len(fft_data_reference))})
    #fft_fig = px.line(pd.concat([fft_df, fft_df_reference]), x=fft_x, y=[fft_df.columns[column_name_index],fft_df_reference.columns[column_name_index]] , labels={"x": "Freq [Hz]"}, title="|FFT|")
    fft_fig = px.line(pd.concat([fft_df, fft_df_reference], axis=1), x=fft_x, y=[fft_df.columns[column_name_index], fft_df_reference.columns[column_name_index]] , labels={"x": "Freq [Hz]"}, title="|FFT|")
    graph_JSON = json.dumps(fft_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON


def generate_compare_psd_graph(freq, compare_value):
    # Parse data
    df = parse_data(freq)
    fs = int(freq)
    df_reference = parse_data(freq, reference = True)
    # Get column index for the corresponding compare_value
    column_name_index = None
    for col_index, col in enumerate(df.columns):
        if compare_value.split("_")[COMPARE_VALUE_TYPE_INDEX].upper() in col: # Get the a/g
            if compare_value.split("_")[COMPARE_VALUE_AXIS_INDEX].upper() in col: # Get the x/y/z
                column_name_index = col_index # Get the index to pull from df

    # TODO Open saved data file and display it with the current sample values

    # Generate graph with selected name
    data = df.to_numpy()
    data_reference = df_reference.to_numpy()
    # PSD (Welch's method) for the desired bin width
    #bin_width = 0.05 # The desired frequency bin width in Hz (must be >= freq_step)
    freq_step = fs/len(data)
    bin_width = freq_step*5
    psd_x, psd_data = signal.welch(data[:, :-1], fs=fs, nperseg=round(fs/bin_width), axis=0)
    psd_x_reference, psd_data_reference = signal.welch(data_reference[:, :-1], fs=fs, nperseg=round(fs/bin_width), axis=0)
    psd_data = np.transpose(psd_data)
    psd_data_reference = np.transpose(psd_data_reference)

    # Skip DC point - MAKES GRAPH READABLE MAY NOT BE VALID
    psd_x = psd_x[1:]
    psd_data = psd_data[:, 1:]
    psd_data_reference = psd_data_reference[:, 1:]

    psd_df = pd.DataFrame({df.columns[i]: psd_data[i] for i in range(len(psd_data))})
    psd_df_reference = pd.DataFrame({df_reference.columns[i]: psd_data_reference[i] for i in range(len(psd_data_reference))})

    psd_fig = px.line(pd.concat([psd_df, psd_df_reference], axis=1), x=psd_x, y=[psd_df.columns[column_name_index],psd_df_reference.columns[column_name_index]], labels={"x": "Freq [Hz]"}, title="PSD")
    psd_fig.update_layout(yaxis_title="[value^2/Hz]") # Needs to be separate

    graph_JSON = json.dumps(psd_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON


def generate_time_json(freq='1600'):
    df = parse_data(freq)
    #print(df)

    fig = px.line(df, x=df.columns[-1], y=df.columns[0:-1], title="Time Domain")

    graph_JSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON

def generate_fft_json(freq='1600'):
    fs = int(freq)
    # Parse data and convert to numpy for fft analysis
    df = parse_data(freq)
    data = df.to_numpy()

    fft_data = np.transpose(np.fft.rfft(data[:, :-1], axis=0, norm="forward")) # Display traces for all params (normalized by length)
    fft_data = np.abs(fft_data) # Magnitude

    # Double non-DC components to account for neg frequencies
    fft_data[:, 1:] *= 2

    fft_x = np.fft.rfftfreq(len(data), 1/fs)

    # Skip DC point - MAKES GRAPH READABLE MAY NOT BE VALID
    fft_x = fft_x[1:]
    fft_data = fft_data[:, 1:]
    
    fft_df = pd.DataFrame({df.columns[i]: fft_data[i] for i in range(len(fft_data))})
    fft_fig = px.line(fft_df, x=fft_x, y=fft_df.columns, labels={"x": "Freq [Hz]"}, title="|FFT|")
    graph_JSON = json.dumps(fft_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON


def generate_psd_json(freq='1600'):
    fs = int(freq)
    # Parse data and convert to numpy for fft analysis
    df = parse_data(freq)
    data = df.to_numpy()
    # PSD (Welch's method) for the desired bin width
    #bin_width = 0.05 # The desired frequency bin width in Hz (must be >= freq_step)
    freq_step = fs/len(data)
    bin_width = freq_step*5
    psd_x, psd_data = signal.welch(data[:, :-1], fs=fs, nperseg=round(fs/bin_width), axis=0)
    psd_data = np.transpose(psd_data)

    # Skip DC point
    #psd_x = psd_x[1:]
    #psd_data = psd_data[:, 1:]

    psd_df = pd.DataFrame({df.columns[i]: psd_data[i] for i in range(len(psd_data))})

    psd_fig = px.line(psd_df, x=psd_x, y=psd_df.columns, labels={"x": "Freq [Hz]"}, title="PSD")
    psd_fig.update_layout(yaxis_title="[value^2/Hz]") # Needs to be separate

    graph_JSON = json.dumps(psd_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_JSON

# Run flask
app.run(debug=False)
#app.run(debug=False, use_evalex=False, host='0.0.0.0')