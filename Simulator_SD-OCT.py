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
# Constants
c0 = 299792458                          # speed of light in vacuum[m/sec]
n1 = 1.00                               # refractive index of air
n2 = 1.46                               # refractive index of cellophane 
ta1 = 150e-3                            # thickness of air
ta2 = 30e-6                             # thickness of air
tc = 50e-6                              # thickness of cellophane(50µm)

# Memo
# GR...st=200 ed=667 (350~700) WH...st=200 ed=900 (350~860) FL...st=404 ed=613
st = 200
ed = 900

# Data loading
name = ['wl','bg','sp']
data = pd.read_csv('data/211007_WH.csv', header=3, index_col=0, names=name)
wl = data.loc[st:ed,'wl']*1e-9          # wavelength
bg = data.loc[st:ed,'bg']               # background spectra
sp = data.loc[st:ed,'sp']               # sample spectras
sp = np.sqrt(sp)                        # amplitude

# Calculation base on constants
R = ((n2-n1)/(n1+n2))**2                # reflectace
T = 1-R                                 # transmittance
wl_c = wl/n2                            # wavelength in cellophane
phase_diff = (ta1%wl)/wl*2*np.pi+np.pi
one_cycle = np.arange(0, 1, 1e-3)*2*np.pi
itf = np.empty_like(wl)

# Calculation the interference
for i in range(len(wl)):
    light_ref = sp.values[i]*np.sin(one_cycle)

    # Light from surface of 1st cellophane
    light_s1 = sp.values[i]*R*np.sin(one_cycle+phase_diff.values[i]+np.pi)

    # Light throught the 1st cellophane
    lp1 = (((2*tc)%wl_c.values[i])/wl_c.values[i])*2*np.pi
    light1 = sp.values[i]*T**2*R*np.sin(one_cycle+phase_diff.values[i]+lp1)

    # Light from surface of 2nd cellophane
    lp2 = (((2*ta2)%wl_c.values[i])/wl_c.values[i])*2*np.pi
    light_s2 = sp.values[i]*T**4*R*np.sin(one_cycle+2*np.pi+lp1+lp2)

    # Light throught the 2nd cellophane
    light2 = sp.values[i]*T**6*R*np.sin(one_cycle+2*lp1+lp2)
    
    # check = (light_ref+light_s1+light1)**2           # cellophane=1
    
    check = (light_ref+light_s1+light1+light_s2+light2)**2     # cellophane=2

    itf[i] = np.amax(check)

# Subtract sample light from interference
itf_new = itf-sp**2

# Resampling (Conversion the x-axis)
freq_fixed,itf_fixed = Resampling(wl,itf_new)

# Generate ascan
depth,result = inverse_ft(freq_fixed*1e-9, itf_fixed, 0.2, n2)

# Generate ascan
sigpro = SignalProcessor(wl, 1.46)
re = sigpro.generate_ascan(itf, sp)
x = sigpro.depth

# Show graphs
plt.plot(wl*1e9, sp**2)
plt.plot(wl*1e9, itf)
plt.title('Interference',fontsize=18)
plt.xlabel('Wavelength [nm]',fontsize=16)
plt.ylabel('Intensity [-]',fontsize=16)
plt.show()

plt.plot(freq_fixed*1e-9,itf_fixed)
plt.title('Resampling',fontsize=18)
plt.xlabel('Frequency[THz]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()

fig1 = plt.figure(figsize=(7, 7))
plt.subplots_adjust(wspace=0.4, hspace=0.4)
ax1 = fig1.add_subplot(211)
ax1.plot(x*1e12, re)
ax1.set_title('A-scan',fontsize=18)
ax1.set_xlabel('Depth [mm]',fontsize=16)
ax1.set_ylabel('Intensity [-]',fontsize=16)

ax2 = fig1.add_subplot(212)
ax2.plot(depth, result)
ax2.set_title('A-scan',fontsize=18)
ax2.set_xlabel('Depth [mm]',fontsize=16)
ax2.set_ylabel('Intensity [-]',fontsize=16)
plt.show()
