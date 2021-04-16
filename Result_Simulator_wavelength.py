import numpy as np
import matplotlib.pyplot as plt

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
tg=[0.1e-3,0.5e-3,1e-3,2e-3]       #thickness of glass[m]
ta=50e-3      #thickness of air[m] 
wlmin=1501e-9 #minimum sweep wavelength[m]
wlmax=1574.9e-9 #maximum sweep wavelength[m]
wlstep=0.1e-9    #sweep wavelength step[m]
ref_times=5   #how many times the light refrects in the glass in calculation
li=100        #light intensity[-]
condition=['0.1[mm]','0.5[mm]','1.0[mm]','2.0[mm]']

R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance
c=c0/n2               #speed of light in glass[m/sec]

wl=np.arange(wlmin,wlmax,wlstep)
itf=np.empty_like(wl)
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
x=np.linspace(0,1,len(itf))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

for k in range(len(condition)):
    for i in range(len(wl)):
        wl_g=wl[i]/n2

        #reference light
        check=li*np.sin(one_cycle*2*np.pi)

        #light refrected on the surface
        lp_surface_rev=((ta%wl[i])/wl[i])*2*np.pi+np.pi #lastphase@reversed due to refrection
        check+=li*R*np.sin(2*np.pi*one_cycle+lp_surface_rev)

        #light refrected after transmitt the glass
        lp=[None]*ref_times
        for j in range(len(lp)):
            lp[j]=((tg[k]*2*(j+1))%wl_g)/wl_g*2*np.pi+lp_surface_rev #last phase
            check+=amp[j]*np.sin(2*np.pi*one_cycle+lp[j])
        itf[i]=np.amax(np.abs(check))
        itf_wf=wf*itf
        
        print(wl[i],'[nm],',condition[k],'completed.')

    result=np.abs(np.fft.ifft(itf_wf))
    plt.plot(x,result,label=condition[k])

plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.ylim(0,45)
plt.xlim(0.5,1)
plt.legend()
plt.show()