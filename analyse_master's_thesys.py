import numpy as np
import matplotlib.pyplot as plt

data=np.loadtxt("data/210729.csv",delimiter=",",encoding='utf-8_sig')
data_nosample=np.loadtxt("data/210729_ref.csv",delimiter=",",encoding='utf-8_sig')
freq = data[:,0] # wavelength
no_sample=data_nosample[:,1]
itf = data[:,1]  # interference spectra
itf-=no_sample

x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)
itf_wf=itf*wf
c0=299792458  #speed of light in vacuum[m/sec]

#x-axis calculation
xmax=1 #x-axis maximum value[mm]
n1=1.4
depth_axis=np.linspace(0,xmax,int(1e2))
time=2*(n1*depth_axis*1e-3)/c0

for j in range(len(freq)):
    if j==0:
        result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    else:
        result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
result/=np.amax(result)

plt.plot(depth_axis,abs(result))
plt.xlabel('Depth [mm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()


