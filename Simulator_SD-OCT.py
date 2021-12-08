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
n0 = 1.00                               # refractive index of air
n1 = 1.38                               # refractive index of csample1
n2 = 1.33                               # refractive index of csample2
ta1 = 150e-3                            # thickness of air
ta2 = 10e-6                             # thickness between samples
tc1 = 20e-6                             # thickness of sample1
tc2 = 30e-6                             # thickness of sample2

# Memo : GR...st=200 ed=667 (350~700) WH...st=200 ed=900 (350~860) FL...st=404 ed=613
st = 200
ed = 667

# Data loading
name = ['wl','bg','sp']
data = pd.read_csv('data/211007_GR.csv', header=3, index_col=0, names=name)
wl = data.loc[st:ed,'wl']*1e-9          # wavelength
bg = data.loc[st:ed,'bg']               # background spectra
sp = data.loc[st:ed,'sp']               # sample spectras
sp = np.sqrt(sp)                        # amplitude

# Calculation base on constants
R0 = ((n1-n0)/(n0+n1))**2                # reflectance air and sample1
T0 = 1-R0                                # transmittance
R1 = ((n2-n1)/(n1+n2))**2                # reflectance sample1 and sample2
T1 = 1-R1                                # transmittance
R2 = ((n0-n2)/(n2+n0))**2                # reflectance air and sample2
T2 = 1-R2                                # transmittance
wl_1 = wl/n1                             # wavelength in sample1
wl_2 = wl/n2                             # wavelength in sample2
phase_diff = (ta1%wl)/wl*2*np.pi+np.pi
one_cycle = np.arange(0, 1, 1e-3)*2*np.pi
itf = np.empty_like(wl)
ref = np.empty_like(wl)

# Calculation the interference
for i in range(len(wl)):
    light_ref = 30*R0*sp.values[i]*np.sin(one_cycle+phase_diff.values[i])

    # Light from surface of 1st sample
    light_s1 = sp.values[i]*R0*np.sin(one_cycle+phase_diff.values[i]+np.pi)

    # Light throught the 1st sample
    lp1 = (((2*tc1)%wl_1.values[i])/wl_1.values[i])*2*np.pi
    light1 = sp.values[i]*T0**2*R0*np.sin(one_cycle+phase_diff.values[i]+lp1)*0.99

    # Light from surface of 2nd sample
    lp2 = (((2*ta2)%wl.values[i])/wl.values[i])*2*np.pi
    light_s2 = sp.values[i]*(T0**2)*(T0**2)*R2*np.sin(one_cycle+phase_diff.values[i]+lp1+lp2+np.pi)*0.9

    # Light throught the 2nd sample
    lp3 = (((2*tc2)%wl_2.values[i])/wl_2.values[i])*2*np.pi
    light2 = sp.values[i]*(T0**4)*(T2**2)*R2*np.sin(one_cycle+phase_diff.values[i]+lp1+lp2+lp3)*0.7
    
    # check = (light_ref+light_s1+light1)**2                     # sample=1
    
    check = (light_ref+light_s1+light1+light_s2+light2)**2     # sample=2
    reference = light_ref**2

    itf[i] = np.amax(check)
    ref[i] = np.amax(reference)

# Subtract sample light from interference
itf_new = itf - ref

# Resampling (Conversion the x-axis)
freq_fixed,itf_fixed = Resampling(wl,itf_new)

# Generate ascan
depth,result = inverse_ft(freq_fixed*1e-9, itf_fixed, 0.1, n1)

# Show graphs
plt.plot(wl*1e9, sp**2, lw=1)
plt.plot(wl*1e9, itf, lw=1)
plt.title('Interference',fontsize=20)
plt.xlabel('Wavelength [nm]',fontsize=20)
plt.ylabel('Intensity [a.u.]',fontsize=20)
plt.xticks(np.arange(400, 701, 100), fontsize=15)
plt.show()

fig1 = plt.figure(figsize=(7, 7))
plt.subplots_adjust(wspace=0.4, hspace=0.4)
ax1 = fig1.add_subplot(211)
ax1.plot(freq_fixed*1e-9, itf_fixed)
ax1.set_title('Resampling',fontsize=20)
ax1.set_xlabel('Frequency [THz]',fontsize=20)
ax1.set_ylabel('Intensity [a.u.]',fontsize=20)

ax2 = fig1.add_subplot(212)
ax2.plot(depth*1e3, result)
ax2.set_xlabel('Depth [μm]',fontsize=20)
ax2.set_ylabel('Intensity [a.u.]',fontsize=20)
ax2.tick_params(labelsize=15)
plt.show()
