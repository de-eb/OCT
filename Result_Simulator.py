import numpy as np
import matplotlib.pyplot as plt

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
tg=[0.1e-3,0.5e-3,1e-3,2e-3]       #thickness of glass[m]
ta=50e-3      #thickness of air[m] 
fmin=190.3492 #minimum sweep frequency[THz]
fmax=199.7332 #maximum sweep frequency[THz]
fstep=1e-3    #sweep frequency step[THz]
ref_times=5   #how many times the light refrects in the glass in calculation
li=100        #light intensity[-]
condition=['0.1[mm]','0.5[mm]','1.0[mm]','2.0[mm]']

R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance
c=c0/n2               #speed of light in glass[m/sec]

freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)
amp=[None]*ref_times
for i in range(len(amp)):
    amp[i]=li*T**2*R**i

#x-axis calculation
freq_calc=1e12*freq
time=1./(np.amax(freq_calc)-np.amin(freq_calc))*np.arange(0,len(freq_calc))
depth=((time*c0)/2*n2)*1e3
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq_calc)/2)]

#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

for k in range(len(condition)):
    for i in range(len(freq)):
        wl_a=c0/freq[i]*1e-12 #wavelength of incident wave[m](air)
        wl_g=c/freq[i]*1e-12 #wavelength of incident wave[m](glass)

        #reference light
        check=li*np.sin(one_cycle*2*np.pi)

        #light refrected on the surface
        lp_surface_rev=((ta%wl_a)/wl_a)*2*np.pi+np.pi #lastphase@reversed due to refrection
        check+=li*R*np.sin(2*np.pi*one_cycle+lp_surface_rev)

        #light refrected after transmitt the glass
        lp=[None]*ref_times
        for j in range(len(lp)):
            lp[j]=((tg[k]*2*(j+1))%wl_g)/wl_g*2*np.pi+lp_surface_rev #last phase
            check+=amp[j]*np.sin(2*np.pi*one_cycle+lp[j])
        itf[i]=np.amax(np.abs(check))
        itf_wf=wf*itf
        
        print(freq[i],'[THz],',condition[k],'completed.')

    result=np.abs(np.fft.ifft(itf_wf))
    plt.plot(depth,result,label=condition[k])

plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.ylim(0,45)
plt.xlim(0,np.amax(depth))
plt.legend()
plt.show()