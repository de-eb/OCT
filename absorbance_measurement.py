import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12,PmaError
from modules.signal_processing_hamasaki import calculate_absorbance
from multiprocessing import Process, Queue

# Graph settings
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

q=Queue()
g_key=None
def on_key(event,q):
    global g_key
    g_key=event.key
    q.put(g_key)
    
#device connection
pma=Pma12(dev_id=5)
data=np.zeros_like(pma.wavelength,dtype=float)
incidence=None
absorbance=np.zeros_like(pma.wavelength,dtype=float)
key=None
err=False

# Graph initialization
fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))  # Key event
ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
ax0_0, = ax0.plot(pma.wavelength,data, label='Transmitted light')
ax0_1, = ax0.plot(pma.wavelength,data, label='Incident light')
ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
ax1 = fig.add_subplot(212, title='Absorbance', xlabel='wavelength [mm]', ylabel='Absorbance [-]')
ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
ax1_0, = ax1.plot(pma.wavelength,absorbance)
ax0.set_yscale("log")

pma.set_parameter(shutter=1)
while g_key!='escape':
    try :data=pma.read_spectra()
    except PmaError as e:
        err=True
        print(e,end="\r")
    else:
        if err:
            print("                            ", end="\r")
            err= False
    ax0_0.set_data(pma.wavelength,data)
    if incidence is None:
        ax0.set_ylim(0,np.amax(data)*1.2)

    if g_key=='enter':
        incidence=pma.read_spectra(averaging=100)
        ax0_1.set_data(pma.wavelength,incidence)
        ax0.set_ylim(0,np.amax(incidence)*1.2)
        print("Incident light spectra updated.")
    
    if incidence is not None:
        absorbance=calculate_absorbance(data,incidence)
        ax1_0.set_data(pma.wavelength,absorbance)
        ax1.set_ylim(0,np.nanmax(absorbance)*1.2)
        
    g_key=None
    plt.pause(0.0001)