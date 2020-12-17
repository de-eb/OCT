import numpy as np
import matplotlib.pyplot as plt

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
tg=[0.1e-3,0.5e-3,1e-3,2e-3]       #thickness of glass[m]
condition=['0.1[mm]','0.5[mm]','1.0[mm]','2.0[mm]']
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2548 #maximum sweep frequency[THz]
fstep=2e-3  #sweep frequency step[THz]
xmax=2.5e-3    #x-axis length[m]
phase_diff=0 #phase difference between reference and sample light

c=c0/n2               #speed of light in glass[m/sec]
freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi

#x-axis calculation
depth=np.linspace(0,xmax*1e3,len(freq))
time=(n2*depth*1e-3)/c0

ref=np.sin(one_cycle) #reference light
#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

for i in range(len(tg)):
    for j in range(len(freq)):
        wl_g=c/freq[j]*1e-12 #wavelength of incident wave[m](glass)

        #light from surface
        #light_sur=np.sin(one_cycle+phase_diff)
        light_sur=0

        #light throught the glass
        lp=((tg[i]%wl_g)/wl_g)*2*np.pi
        #light_thr=np.sin(one_cycle+phase_diff+lp)
        light_thr=0

        check=(ref+light_sur+light_thr)**2
        itf[j]=np.amax(check)-1
        itf_wf=itf*wf

        #if j%100==0:
        #    print(freq[j])
        #    plt.plot(one_cycle,ref,label='reference light')
        #    plt.plot(one_cycle,light_sur,label='light from surface')
        #    plt.plot(one_cycle,light_thr,label='light throught the glass')
        #    plt.legend()
        #    plt.xlabel('phase')
        #    plt.show()

    #inverse ft
    for j in range(len(freq)):
        if j==0:
            result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
        else:
            result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    result/=len(freq)
    plt.plot(depth,abs(result),label=condition[i])
plt.legend()
plt.xlabel('depth[mm]')
plt.show()

