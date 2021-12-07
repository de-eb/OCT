import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from modules.signal_processing import SignalProcessor
from pycubicspline import *

def Resampling(wl,itf):
    """Resampling function for OCT.
    
        Parameters
        ----------
        wl : `ndarray`
            wavelength data[nm]
        itf : `ndarray`
            measured interference data[arb. unit]
        
        Returns
        -------
        freq_fixed : `ndarray`
            calculated frequency data[THz] 
        itf_fixed : `ndarray`
            fixed interference data[arb. unit]
        
        Requirement
        -------
        pycubicspline.py (from pycubicspline import *)
    """
    freq=(299792458/(wl*1e9))*1e6
    spline=Spline(np.flipud(freq),np.flipud(itf))
    freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,int(1e5))
    itf_fixed=[spline.calc(i) for i in freq_fixed]
    for i in range(len(itf_fixed)):
        if itf_fixed[i]==None:
            itf_fixed[i]=0
    return freq_fixed,itf_fixed

def inverse_ft(freq, itf, xmax, n):
    """Inverse Fourier transform function for OCT.
    
        Parameters
        ----------
        freq : `ndarray`
            frequency data[THz]
        itf : `ndarray`
            measured interference data[arb. unit]
        xmax : `float`
            maximum value of depth axis[mm]
        n : `float`
            refractive index of sample
        
        Returns
        -------
        depth_axis : `ndarray`
            calculated depth axis[mm]
        result : `ndarray`
            transformed data[arb. unit]
    """
    depth_axis = np.linspace(0, xmax, int(1e5))
    time = 2*(n*depth_axis*1e-3)/299792458
    for i in range(int(len(freq)/10)):
        if i==0:
            result = itf[i*10]*np.sin(2*np.pi*time*freq[i*10]*1e12)
        else:
            result += itf[i*10]*np.sin(2*np.pi*time*freq[i*10]*1e12)
    result /= len(freq)
    return depth_axis, abs(result)

# refractive index of sample
n = 1.46                               

# Memo : GR...st=200 ed=667 (350~700) WH...st=200 ed=900 (350~860) FL...st=404 ed=613
st = 320
ed = 532

# Data loading
name = ['wl','bg','sp']
data = pd.read_csv('data/211103_cell+air.csv', header=3, index_col=0, names=name)
wl = data.loc[st:ed,'wl']*1e-9          # wavelength
bg = data.loc[st:ed,'bg']               # background spectra
sp = data.loc[st:ed,'sp']               # sample spectras

# Subtract sample light from interference
itf_new = sp - bg

# Resampling (Conversion the x-axis)
freq_fixed,itf_fixed = Resampling(wl,itf_new)

# Generate ascan
depth,result = inverse_ft(freq_fixed*1e-9, itf_fixed, 0.2, n)

# Show graphs
plt.plot(wl*1e9, sp)
plt.plot(wl*1e9, bg)
plt.title('Interference',fontsize=18)
plt.xlabel('Wavelength [nm]',fontsize=16)
plt.ylabel('Intensity [-]',fontsize=16)
plt.show()

fig1 = plt.figure(figsize=(7, 7))
plt.subplots_adjust(wspace=0.4, hspace=0.4)
ax1 = fig1.add_subplot(211)
ax1.plot(freq_fixed*1e-9, itf_fixed)
ax1.set_title('Resampling',fontsize=18)
ax1.set_xlabel('Frequency [THz]',fontsize=16)
ax1.set_ylabel('Intensity [-]',fontsize=16)

ax2 = fig1.add_subplot(212)
ax2.plot(depth, result)
ax2.set_title('A-scan',fontsize=18)
ax2.set_xlabel('Depth [mm]',fontsize=16)
ax2.set_ylabel('Intensity [-]',fontsize=16)
plt.show()
