import numpy as np
import pandas as pd
import plotly.express as px
import scipy.signal as signal

def show_graphs(df, fs):
    data = df.to_numpy() # Or pass in data array as well as df
    
    # Time domain
    fig = px.line(df, x=df.columns[-1], y=df.columns[0:-1], markers=False, title="Time Domain")
    fig.show()


    # Frequency domain (FFT)
    fft_data = np.transpose(np.fft.rfft(data[:, :-1], axis=0, norm="forward")) # Display traces for all params (normalized by length)
    fft_data = np.abs(fft_data) # Magnitude

    # Double non-DC components to account for neg frequencies
    fft_data[:, 1:] *= 2

    fft_x = np.fft.rfftfreq(len(data), 1/fs)
    
    fft_df = pd.DataFrame({df.columns[i]: fft_data[i] for i in range(len(fft_data))})
    fft_fig = px.line(fft_df, x=fft_x, y=fft_df.columns, labels={"x": "Freq [Hz]"}, title="|FFT|")
    fft_fig.show()


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
    psd_fig.show()
