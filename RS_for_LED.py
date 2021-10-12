import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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


#memo
#GR...st=300 ed=600
#WH...st=200 ed=900
st=300
ed=600

#data loading
name=['wl','bg','sp']
data=pd.read_csv('data/211007_GR.csv', header=3, index_col=0,names=name)
wl=data.loc[st:ed,'wl']*1e-9      # Wavelength
bg=data.loc[st:ed,'bg']           # Background spectra
sp=data.loc[st:ed,'sp']           # Sample spectra

#constants
c0=299792458    #speed of light in vacuum[m/sec]
n1=1.0          #refractive index of air
n2=1.4          #refractive index of cellophane 
ta=150e-3       #thickness of air
tc=50e-6        #thickness of cellophane(50µm)

#calculation base on constants
R=((n2-n1)/(n1+n2))**2      #reflectace
T=1-R                       #transmittance
wl_c=wl/n2                  #wavelength in cellophane
phase_diff=(ta%wl)/wl*2*np.pi+np.pi
one_cycle=np.arange(0,1,1e-3)*2*np.pi
itf=np.empty_like(wl)
ref=np.sin(one_cycle)

for i in range(len(wl)):
    #light from surface
    light_sur=sp.values[i]*R*np.sin(one_cycle+phase_diff.values[i])

    #light throught the 1st cellophane
    lp1=(((2*tc)%wl_c.values[i])/wl_c.values[i])*2*np.pi
    light1=sp.values[i]*R*T**2*np.sin(one_cycle+phase_diff.values[i]+lp1)

    #light throught the 2nd cellophane
    light2=sp.values[i]*R*T**4*np.sin(one_cycle+phase_diff.values[i]+lp1*2)

    check=(ref+light_sur+light1+light2)**2
    itf[i]=np.amax(check)

plt.plot(wl*1e9,itf)
plt.title('Interference light',fontsize=18)
plt.xlabel('Wavelength[nm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()



# freq_fixed,itf_fixed=Resampling(wl,itf)
# depth,result=inverse_ft(freq_fixed,itf_fixed,0.2,n2)