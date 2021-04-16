import numpy as np
import matplotlib.pyplot as plt
import inverseFourier_hamasaki as ifh 

data=np.loadtxt("data/result_SGGG_0.759mm.csv",delimiter=",",encoding='utf-8_sig')
data_nosample=np.loadtxt("data/result_SGGG_0.759mm_no_sample.csv",delimiter=",",encoding='utf-8_sig')
freq = data[:,0] # wavelength
no_sample=data_nosample[:,1]
itf = data[:,1]  # interference spectra
itf-=no_sample



x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)
itf_wf=itf*wf

c0=299792458  #speed of light in vacuum[m/sec]
'''
#x-axis calculation
xmax=20e-3
n1=1.92
depth_axis=np.linspace(0,xmax*1e3,int(1e5))
time=2*(n1*depth_axis*1e-3)/c0

for j in range(len(freq)):
    if j==0:
        result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    else:
        result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
result/=len(freq)

plt.plot(depth_axis,abs(result))
plt.xlabel('Depth [mm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()
'''
ifh.inverse_ft_plot(freq,itf_wf,20e-3,1.92)
plt.xlabel('Depth [mm]',fontsize=16)
plt.ylabel('Intensity [arb. unit]',fontsize=16)
plt.show()
