import numpy as np
import pandas as pd
import plotly.express as px
import scipy.signal as signal # For PSD calculations

# Check calculation results using generated inputs

# https://info.endaq.com/hubfs/Plots/enDAQ-Vibration-Monitoring-Metrics-Case-Western-Bearing-Data_2.html used as reference for improving some calculations


mode = "PSD2" #"FFT", "PSD", "PSD2"
add_noise = "Combo" #True, False, "Combo"

#sample_duration = 10; sample_count = 50
#sample_duration = 10; sample_count = 1000
sample_duration = 100; sample_count = 10000
#sample_duration = 55; sample_count = 5500

data_time = np.linspace(0, sample_duration, sample_count, endpoint=False)
omega = 2*np.pi*data_time
data = [
    np.cos(data_time),
    np.cos(3*data_time),
    np.cos(omega),
    np.cos(2*omega),
    0.7+0*data_time,
    0.5+0.5*np.cos(omega),
    np.cos(0.4*omega) + np.cos(1.5*omega),
    data_time
]
column_names = ["Cos(t)", "Cos(3t)", "Cos(ω=2πt)", "Cos(2ω)", "0.7", "0.5+0.5Cos(ω)", "Cos(0.4ω)+Cos(1.5ω)", "Time"]

if add_noise:
    np.random.seed(1) # Constant noise for comparison/validation of different calculations
    noise = np.random.randn(sample_count) * 10**(-10/20)
    for i in range(len(data)-1):
        if add_noise == "Combo":
            data.insert(i*2+1, data[i*2] + noise)
            column_names.insert(i*2+1, column_names[i*2] + " + Noise")
        else:
            data[i] += noise

data = np.transpose(data)
df = pd.DataFrame(data, columns=column_names)

fig = px.line(df, x=df.columns[-1], y=df.columns[0:-1], markers=False, title="Time Domain", range_x=[0,10])
fig.show()

freq_data = np.transpose(np.fft.rfft(data[:, :-1], axis=0, norm="forward")) # Display traces for all params (normalized by length)
freq_data = np.abs(freq_data) # Magnitude

# Double non-DC components to account for neg frequencies
freq_data *= 2 #/ len(data_time) # Already normalized by sample length above in fft
freq_data[:, 0] /= 2

freq_step = 1/(data[-1, -1] - data[0, -1])
freq_step *= 1 - 1/len(data) # Correct frequency step to account for full effective sample length (hopefully valid, seems to produce correct result)

#np.fft.rfftfreq(len(data), 1/freq_step/len(data))
freq_x = [x * freq_step for x in range(len(freq_data[0]))]

if mode == "FFT":
    pass # Already have magnitude
elif mode == "PSD":
    freq_data = freq_data**2/freq_step/2 # PSD simple from FFT (1/2 factor for RMS value)
elif mode == "PSD2":
    # Seems nearly identical to calculation above except for f=0(DC) and slight diff at f_max, at least with default parameters
    #freq_data = [signal.periodogram(data[:, i], len(data)*freq_step)[1] for i in range(len(data[0])-1)]
    #freq_x, freq_data_t = signal.periodogram(data[:, :-1], len(data)*freq_step, axis=0)
    #freq_data = np.transpose(freq_data_t)
    
    # Use Welch's method to compute PSD for the desired bin width
    bin_width = 0.05 # The desired frequency bin width in Hz (must be >= freq_step)
    fs = len(data)*freq_step #= sample_count/sample_duration
    # Round to prevent large effect from tiny rounding error when floored
    #freq_x, freq_data_t = signal.welch(data[:, :-1], fs=fs, nperseg=len(data)//5, axis=0)
    freq_x, freq_data_t = signal.welch(data[:, :-1], fs=fs, nperseg=round(fs/bin_width), axis=0)
    freq_data = np.transpose(freq_data_t)
    
    # Integrate PSD over frequency and convert to amplitude (messy with multiple signals or noise)
    #mags = (np.sum(freq_data, axis=1)*bin_width*2)**0.5
    
    # Integrate PSD over 5 closest frequencies to max value and convert to amplitude (will only find one peak)
    #max_indices = np.argmax(freq_data, axis=1)
    #peak_sum = [np.sum(freq_data[i][max(0,max_indices[i]-2):max_indices[i]+3]) for i in range(len(freq_data))]
    #mags = (np.array(peak_sum)*bin_width*2)**0.5 # Factor of 2 for RMS to amplitude
    # Determine frequency for each peak from above
    #p_freqs_simple = freq_x[max_indices]
    # Weighted average of 5 nearest frequencies
    #p_freqs = [np.sum(freq_x[max(0,max_indices[i]-2):max_indices[i]+3]
    #                 * freq_data[i][max(0,max_indices[i]-2):max_indices[i]+3])
    #               / peak_sum[i] for i in range(len(freq_data))]
    # Combine two versions by using simple result if very close to weighted result (ignore nearby freqs if peak dominates)
    #peak_freqs_combo = [p_freqs_simple[i] if abs(1 - p_freqs_simple[i]/p_freqs[i]) < 0.01 else p_freqs[i] for i in range(len(freq_data))]
    # Ignore any peaks that have too small of a magnitude and treat signal as DC
    #peak_freqs_combo = [peak_freqs_combo[i] if mags[i] > 1e-3 and peak_sum[i] > 0.1*np.sum(freq_data[i]) else 0 for i in range(len(freq_data))]
    #peak_freqs_combo = np.round(peak_freqs_combo, 6).tolist()

# Skip DC point
#freq_x = freq_x[1:] #freq_x.pop(0)
#freq_data = freq_data[:, 1:]

# Compute cumulative RMS for comparisons
#for i in range(len(freq_data)):
#   freq_data[i] = np.cumsum(freq_data[i])

freq_df = pd.DataFrame({df.columns[i]: freq_data[i] for i in range(len(freq_data))})

if mode == "FFT":
    freq_fig = px.line(freq_df, x=freq_x, y=freq_df.columns, log_y=False, markers=False, range_x=[0,2.5], labels={"x": "Freq [Hz]", "y": "Acceleration [g]"}, title="|FFT|")
else:
    freq_fig = px.line(freq_df, x=freq_x, y=freq_df.columns, log_y=False, markers=False, range_x=[0,2.5], labels={"x": "Freq [Hz]", "y": "Acceleration [g^2/Hz]"}, title="PSD") #title=mode
    freq_fig.update_layout(yaxis_title="[value^2/Hz]") # Needs to be separate
freq_fig.show()
