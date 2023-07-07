import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12,PmaError
from modules.signal_processing_hamasaki import calculate_reflectance 
from multiprocessing import Process, Queue
import modules.data_handler as dh
import warnings

# グラフ設定
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams["xtick.minor.visible"] = True
plt.rcParams["ytick.minor.visible"] = True
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams["xtick.minor.width"] = 0.5
plt.rcParams["ytick.minor.width"] = 0.5
plt.rcParams['font.size'] = 14
plt.rcParams['axes.linewidth'] = 1.0

q = Queue()
g_key = None
def on_key(event,q):
    global g_key
    g_key = event.key
    q.put(g_key)

# 使用機器
pma = Pma12(dev_id = 5)
data = np.zeros_like(pma.wavelength,dtype=float)
incidence = None
reflectance = np.zeros_like(pma.wavelength,dtype=float) 
key = None
err = False

# グラフ設定
fig = plt.figure(figsize = (10, 10), dpi = 80, tight_layout = True)
fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))

ax0 = fig.add_subplot(211, title = 'Spectrometer output', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [-]')
ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
ax0.ticklabel_format(style = "sci", axis = "y",scilimits = (0,0))
ax0_0, = ax0.plot(pma.wavelength, data, label = 'Transmitted light') 
ax0_1, = ax0.plot(pma.wavelength, data, label = 'Incident light')
ax0.legend(bbox_to_anchor = (1,1), loc = 'upper right', borderaxespad = 0.2)

ax1 = fig.add_subplot(212, title = 'Transmittance', xlabel = 'Wavelength [mm]', ylabel = 'Transmittance [-]')
ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
ax1.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
ax1_0, = ax1.plot(pma.wavelength, reflectance) 
warnings.simplefilter(action = 'ignore', category = UserWarning)
ax0.set_yscale("log")
ax0.set_xlim(350, 900)
ax1.set_xlim(350, 900)

st = 201
ed = 941

pma.set_parameter(shutter = 1)
while g_key != 'escape':
    try :data = pma.read_spectra()
    except PmaError as e:
        err = True
        print(e, end="\r")
    else:
        if err:
            print("                            ", end="\r")
            err = False
    ax0_0.set_data(pma.wavelength[st:ed], data[st:ed]) #changed

    if incidence is None:
        ax0.set_ylim(1, np.amax(data)*1.2)
    else:
        reflectance = calculate_reflectance(data[st:ed], incidence[st:ed]) #changed

        ax1_0.set_data(pma.wavelength[st:ed], reflectance) #changed
        ax1.set_ylim(0, np.nanmax(reflectance)*1.2) 

    if g_key == 'enter':
        incidence=pma.read_spectra(averaging = 100)
        ax0_1.set_data(pma.wavelength[st:ed], incidence[st:ed]) #changed
        ax0.set_ylim(0, np.amax(incidence)*1.2) 
        print("Incident light spectra updated.")
    
    if g_key == 'alt':
        data = pma.read_spectra(averaging = 100)
        if incidence is None:
            print('Error:Incidence light data is not registered.')
        else:
            dh.save_spectra(pma.wavelength, incidence, data, memo='Attention:This is transmittance measurement data.')
    
    if g_key == 'delete':
        incidence = None
        ax0_1.set_data(pma.wavelength[st:ed], np.zeros_like(pma.wavelength[st:ed])) #changed
        ax1_0.set_data(pma.wavelength[st:ed], np.zeros_like(pma.wavelength[st:ed])) #changed
        print('Incident data daleted.')
        
    g_key = None
    plt.pause(0.0001)