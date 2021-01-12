import numpy as np
import matplotlib.pyplot as plt

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
tg1=1e-3      #thickness of 1st glass[m]
tg2=0.5e-3      #thickness of 2nd glass[m]
tg3=0.5e-3      #thickness of 3rd glass[m]
tg4=0.3e-3   #thickness of 4th glass[m]
tg5=0.2e-3   #thickness of 5th glass[m]
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2548 #maximum sweep frequency[THz]
fstep=2e-3  #sweep frequency step[THz]
xmax=3e-3    #x-axis length[m]
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

for i in range(1):
    for j in range(len(freq)):
        wl_g=c/freq[j]*1e-12 #wavelength of incident wave[m](glass)

        #light from surface
        light_sur=np.sin(one_cycle+phase_diff)
        #light_sur=0

        #light throught the 1st glass
        lp1=((tg1%wl_g)/wl_g)*2*np.pi
        light1=np.sin(one_cycle+phase_diff+lp1)
        #light_thr=0

        #light throught the 2nd glass
        lp2=((tg1+tg2)%wl_g)/wl_g*2*np.pi
        light2=np.sin(one_cycle+phase_diff+lp2)

        #light throught the 3rd glass
        lp3=((tg1+tg2+tg3)%wl_g)/wl_g*2*np.pi
        light3=np.sin(one_cycle+phase_diff+lp3)

        #light throught the 4th glass
        lp4=((tg1+tg2+tg3+tg4)%wl_g)/wl_g*2*np.pi
        light4=np.sin(one_cycle+phase_diff+lp4)

        #light throught the 5th glass
        lp5=((tg1+tg2+tg3+tg4+tg5)%wl_g)/wl_g*2*np.pi
        light5=np.sin(one_cycle+phase_diff+lp5)
        

        check=(ref+light_sur+light1+light2+light3+light4+light5)**2
        itf[j]=np.amax(check)-1
        itf_wf=itf*wf

    #inverse ft
    for j in range(len(freq)):
        if j==0:
            result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
        else:
            result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    result/=len(freq)
    plt.plot(depth,abs(result))
plt.legend()
plt.xlabel('depth[mm]')
plt.xticks(np.arange(0,xmax*1e3,0.5))
plt.show()
