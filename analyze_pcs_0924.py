import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from pycubicspline import *

name=['wl','bg','sp']
st = 333
ed = 533
data=pd.read_csv('data/211103_0.csv', header=3, index_col=0,names=name)
wl=data.loc[st:ed,'wl'] # Wavelength
bg=data.loc[st:ed,'bg'] # Background spectra
sp=data.loc[st:ed,'sp'] # Sample spectra
itf=sp-bg*(np.amax(sp)/np.amax(bg))
#itf=sp-bg
plt.plot(wl,sp,label='interference')
plt.plot(wl,bg,label='reference_before')
plt.plot(wl,bg*(np.amax(sp)/np.amax(bg)),label='reference_after')
plt.legend()
plt.show()


c0=299792458  #speed of light in vacuum[m/sec]
freq=(c0/(wl*1e9))*1e6
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)
itf_wf=itf*wf

spline=Spline(np.flipud(freq),np.flipud(itf))
freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,len(freq)*3)
#freq_fixed=np.arange(np.amin(freq)-1,np.amax(freq)+1,371e-3)
print(len(freq_fixed))
itf_fixed=[spline.calc(i) for i in freq_fixed]
for i in range(len(itf_fixed)):
    if itf_fixed[i]==None:
        itf_fixed[i]=0

plt.plot(freq_fixed,itf_fixed)
plt.xlabel('Frequency[THz]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()

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
    freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,len(wl))
    itf_fixed=[spline.calc(i) for i in freq_fixed]
    for i in range(len(itf_fixed)):
        if itf_fixed[i]==None:
            itf_fixed[i]=0
    return freq_fixed,itf_fixed


#x-axis calculation
xmax=0.2 #x-axis maximum value[mm]
n1=1.4
depth_axis=np.linspace(0,xmax,int(1e5))
time=2*(n1*depth_axis*1e-3)/c0
'''
for j in tqdm(range(int(len(freq_fixed)/10))):
    if j==0:
        result=itf_fixed[j*10]*np.sin(2*np.pi*time*freq_fixed[j*10]*1e12)
    else:
        result+=itf_fixed[j*10]*np.sin(2*np.pi*time*freq_fixed[j*10]*1e12)
result/=np.amax(result)
'''
for j in tqdm(range(int(len(freq_fixed)))):
    if j==0:
        result=itf_fixed[j]*np.sin(2*np.pi*time*freq_fixed[j]*1e12)
    else:
        result+=itf_fixed[j]*np.sin(2*np.pi*time*freq_fixed[j]*1e12)
result/=np.amax(result)

plt.plot(depth_axis,abs(result))
plt.xlabel('Depth [mm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
#plt.ylim(0,0.2)
plt.show()