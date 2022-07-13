import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12,PmaError
from modules.signal_processing_hamasaki import SignalProcessorHamasaki

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

#device connection
pma=Pma12(dev_id=5)
data=np.zeros_like(pma.wavelength,dtype=float)
key=None
err=False

# Graph initialization
fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))  # Key event
ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
ax0_0, = ax0.plot(ccs.wavelength[st:ed], itf[st:ed,0], label='Transmitted light')
ax0_1, = ax0.plot(ccs.wavelength[st:ed], itf[st:ed,0], label='Incident light')
ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
ax1 = fig.add_subplot(212, title='Absorbance', xlabel='depth [mm]', ylabel='Intensity [-]')
ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
ax1_0, = ax1.plot(sp.depth*(10**exponentation), ascan)
ax1.set_xlim(0,np.amax(sp.depth)*(10**exponentation))