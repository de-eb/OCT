import numpy as np
import matplotlib.pyplot as plt

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
tg=[0.1e-3,0.5e-3,1e-3,2e-3]       #thickness of glass[m]
condition=['0.1[mm]','0.5[mm]','1.0[mm]','2.0[mm]']
ta=10e-3      #thickness of air[m] 
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2542 #maximum sweep frequency[THz]
fstep=2e-3  #sweep frequency step[THz]
ref_times=5   #how many times the light refrects in the glass in calculation
li=100        #light intensity[-]
xmax=10e-3    #x-axis length[m]

R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance
c=c0/n2               #speed of light in glass[m/sec]

freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi
amp=[None]*ref_times
for i in range(len(amp)):
    amp[i]=li*T**2*R**i

#x-axis calculation
depth=np.linspace(0,xmax*1e3,len(freq))
time=(2*n2*depth*1e-3)/c0

#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

#reference light
refer=li*np.sin(one_cycle) 

for k in range(len(tg)):
    for i in range(len(freq)):
        wl_a=c0/freq[i]*1e-12 #wavelength of incident wave[m](air)
        wl_g=c/freq[i]*1e-12 #wavelength of incident wave[m](glass)

        #light refrected on the surface
        lp_surface=((ta%wl_a)/wl_a)*2*np.pi #last phase
        light_sur=li*R*np.sin(one_cycle+lp_surface)

        #light refrected after transmitt the glass
        lp=[None]*ref_times
        #for j in range(len(lp)):
        #    tr=tg[k]*2*(j+1)-(1-lp_surface/(2*np.pi))*wl_g
        #    lp[j]=((tr%wl_g)/wl_g)*2*np.pi #last phase
        #    if j==0:
        #        light_trans=amp[j]*np.sin(one_cycle)
        #    check+=amp[j]*np.sin(one_cycle+lp[j]+np.pi)
        for j in range(len(lp)):
            lp[j]=((tg[k]*2*(j+1))/wl_g)*2*np.pi
            if j==0:
                light_trans=amp[j]*np.sin(one_cycle+lp[j]+lp_surface)
            else:
                light_trans+=amp[j]*np.sin(one_cycle+lp[j]+lp_surface)

        itf[i]=np.amax((light_sur+light_trans+refer)**2)-1
        itf_wf=wf*itf
    print('calculation',condition[k],'is completed.')

    #plt.plot(freq,itf,label=condition[k])
    #plt.xlim(190,190.2)

    #inverse ft
    for i in range(len(freq)):
        if i==0:
            result=itf_wf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        else:
            result+=itf_wf[i]*np.sin(2*np.pi*freq[i]*time*1e12)
    result/=len(itf_wf)
    #result=np.fft.ifft(itf_wf)
    plt.plot(depth,np.abs(result),label=condition[k])
    print('inverse fourier transform is completed.')

plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
#plt.ylim(0,20)
plt.legend()
plt.show()