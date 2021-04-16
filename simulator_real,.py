import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

data_nosample=np.loadtxt("data/result_SGGG_0.759mm_no_sample.csv",delimiter=",",encoding='utf-8_sig')
no_sample=data_nosample[:,1]
freq_tender=no_sample*2
freq = data_nosample[:,0]
'''
for i in range(len(no_sample)):
    no_sample[i]=1
'''
c0=299792458  #speed of light in vacuum[m/sec]
n0=1
n1=1.92        #refractive index 
ta=150e-3     #thickness of air
tg=0.759e-3   #thicknes of SGGG

c1=c0/n1            #speed of light in surrounding substance[m/sec]
R=((n1-n0)/(n1+n0))**2 #refrectance of surface
T=1-R                  #transmittance of surface
one_cycle=np.arange(0,1,1e-3)*2*np.pi
itf=np.empty_like(freq)

#x-axis calculation
xmax=1e-3
n1=1.92
depth_axis=np.linspace(0,xmax*1e3,len(freq))
time=2*(n1*depth_axis*1e-3)/c0

#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

for i in range(len(freq)):
    wl_a=c0/freq[i]*1e-12   #wavelenght of incident wave[m](air)
    wl_g=c1/freq[i]*1e-12    #wavelength of incident wave[m](surrounding substance)

    light_ref=freq_tender[i]*np.sin(one_cycle)

    phase_diff=(ta%wl_a)/wl_a*2*np.pi+np.pi
    light_sur=freq_tender[i]*R*np.sin(one_cycle+phase_diff)

    lp=((tg*2)%wl_g)/wl_g*2*np.pi
    light1=R*T**2*freq_tender[i]*np.sin(one_cycle+phase_diff+lp)

    check=(light_sur+light_sur+light1)**2
    itf[i]=np.amax(check)

itf-=no_sample
itf_wf=itf*wf
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