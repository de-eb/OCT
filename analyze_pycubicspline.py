import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pycubicspline import *

data=np.loadtxt("data/210729.csv",delimiter=",",encoding='utf-8_sig')
data_nosample=np.loadtxt("data/210729_ref.csv",delimiter=",",encoding='utf-8_sig')
wl = data[:,0] # wavelength
no_sample=data_nosample[:,1]
itf = data[:,1]  # interference spectra
itf-=no_sample

c0=299792458  #speed of light in vacuum[m/sec]
freq=(c0/(wl*1e9))*1e6
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)
itf_wf=itf*wf

spline=Spline(np.flipud(freq),np.flipud(itf))
freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,int(1e5))
itf_fixed=[spline.calc(i) for i in freq_fixed]
for i in range(len(itf_fixed)):
    if itf_fixed[i]==None:
        itf_fixed[i]=0
print(itf_fixed)

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
        pycubicspline.py
    """
    freq=(299792458/(wl*1e9))*1e6
    spline=Spline(np.flipud(freq),np.flipud(itf))
    freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,int(1e5))
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

for j in tqdm(range(len(freq_fixed))):
    if j==0:
        result=itf_fixed[j]*np.sin(2*np.pi*time*freq_fixed[j]*1e12)
    else:
        result+=itf_fixed[j]*np.sin(2*np.pi*time*freq_fixed[j]*1e12)
result/=np.amax(result)

plt.plot(depth_axis,abs(result))
plt.xlabel('Depth [mm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()

