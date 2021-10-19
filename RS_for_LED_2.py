import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from modules.signal_processing import SignalProcessor
from pycubicspline import *
from scipy.fftpack import fft, fftfreq

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


# Memo
#GR...st=201 ed=667 (350~700)
#WH...st=200 ed=900 (350~860)
#FL...st=404 ed=613
st=201
ed=667

# Data loading
name=['wl','bg','sp']
data=pd.read_csv('data/211007_GR.csv', header=3, index_col=0, names=name)
wl=data.loc[st:ed,'wl']*1e-9     # wavelength
bg=data.loc[st:ed,'bg']          # background spectra
sp=data.loc[st:ed,'sp']          # sample spectras

# Constants
c0=299792458                     # speed of light in vacuum[m/sec]
n1=1.0                           # refractive index of air
n2=1.46                          # refractive index of cellophane 
ta=150e-3                        # thickness of air
tc=50e-6                         # thickness of cellophane(50µm)

# Calculation base on constants
R=((n2-n1)/(n1+n2))**2           # reflectace
T=1-R                            # transmittance
wl_c=wl/n2                       # wavelength in cellophane
phase_diff=(ta%wl)/wl*2*np.pi+np.pi
step = 1/(len(wl))
one_cycle=np.arange(0, 1, step)*2*np.pi
itf=np.empty_like(wl)
ref_s=np.empty_like(wl)

for i in range(len(wl)):
    ref=sp.values[i]*np.sin(one_cycle)

    # Light from surface
    light_sur=sp.values[i]*R*np.sin(one_cycle+phase_diff.values[i])

    # Light throught the 1st cellophane
    lp1=(((2*tc)%wl_c.values[i])/wl_c.values[i])*2*np.pi
    light1=sp.values[i]*R*T**2*np.sin(one_cycle+phase_diff.values[i]+lp1)

    # Light throught the 2nd cellophane
    light2=sp.values[i]*R*T**4*np.sin(one_cycle+phase_diff.values[i]+lp1*2)

    # Reference light
    ref_s = ref
    
    #check=(ref+light_sur+light1)**2           # cellophane=1
    
    check=(ref+light_sur+light1+light2)**2     # cellophane=2

    itf[i]=np.amax(check)

#freq_fixed,itf_fixed=Resampling(wl,itf)

#plt.plot(freq_fixed/1e9,itf_fixed)
#plt.xlabel('Frequency[THz]',fontsize=16)
#plt.ylabel('Intensity [arb. unit]',fontsize=16)
#plt.show()

#depth,result=inverse_ft(freq_fixed*1e-9,itf_fixed,0.2,n2)
#plt.plot(depth,result)
#plt.xlabel('depth[mm]',fontsize=16)
#plt.ylabel('Intensity [-]',fontsize=16)
#plt.show()

# Descrete Fourier Transform
F_itf = fft(itf)
F_ref = fft(ref_s)
freq = (c0/wl)*1e-9

# Graph Show
fig = plt.figure(figsize=(7, 7))
plt.subplots_adjust(wspace=0.2, hspace=0.6)

ax1 = fig.add_subplot(511)
ax1.plot(wl*1e9, bg, sp)
ax1.set_title('Light Source',fontsize=18)
ax1.set_xlabel('Wavelength [nm]',fontsize=16)
ax1.set_ylabel('Intensity [-]',fontsize=16)

ax2 = fig.add_subplot(512)
ax2.plot(wl*1e9, itf)
ax2.set_title('Interference Light',fontsize=18)
ax2.set_xlabel('Wavelength [nm]',fontsize=16)
ax2.set_ylabel('Intensity [-]',fontsize=16)

ax3 = fig.add_subplot(513)
ax3.plot(freq, np.abs(F_itf))
ax3.set_title('DFT_Interference',fontsize=18)
ax3.set_xlabel('Frequency [GHz]',fontsize=16)
ax3.set_ylabel('Amplitude',fontsize=16)

ax4 = fig.add_subplot(514)
ax4.plot(freq, np.abs(F_ref))
ax4.set_title('DFT_Reference',fontsize=18)
ax4.set_xlabel('Frequency [GHz]',fontsize=16)
ax4.set_ylabel('Amplitude',fontsize=16)

# Generate ascan & coversion depth
sp = SignalProcessor(wl, 1.46)
re = sp.generate_ascan(itf, bg)
x = sp.depth

ax5 = fig.add_subplot(515)
ax5.plot(x*1e12, re)
ax5.set_title('A-scan',fontsize=18)
ax5.set_xlabel('Depth [μm]',fontsize=16)
ax5.set_ylabel('Intensity [-]',fontsize=16)
plt.show()
