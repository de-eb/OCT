import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.fftpack import ifft

data=np.loadtxt("data/200902_0.csv",delimiter=",")
wl = data[:,0] # wavelength
itf = data[:,1]  # interference spectra

#windowfunction
x=np.linspace(0,1,len(wl))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

plt.xlabel("depth[m]")
plt.ylabel("light intensity")
#ax=plt.subplot()
#ax.set_ylim(0,0.2)
#ax.set_xlim(0,1)



#windowfunction processing
itf_wp=itf*wf

tmp=np.abs(np.fft.ifft(itf_wp))
#y-axis processing
#time=(1/wl)*3e8
#depth=(time*3e8)/2
freq=3e8/wl
time=(1./freq)*1e6
time=(np.amax(time)-time)*1000
time/=1e9
time*=3e8

plt.plot(time,tmp)
plt.show()