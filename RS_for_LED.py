import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st=200
ed=900

#data loading
name=['wl','bg','sp']
data=pd.read_csv('data/211007_WH.csv', header=3, index_col=0,names=name)
wl=data.loc[st:ed,'wl']*1e-9 # Wavelength
bg=data.loc[st:ed,'bg'] # Background spectra
sp=data.loc[st:ed,'sp'] # Sample spectra
plt.plot(sp)
plt.show()

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.4        #refractive index of cellophane 
ta=150e-3       #thickness of air
tc=50e-6        #thickness of cellophane(50µm)

#calculation base on constants
R=((n2-n1)/(n1+n2))**2      #reflectace
T=1-R                       #transmittance
wl_c=wl/n2                  #wavelength in cellophane
phase_diff=(ta%wl)/wl*2*np.pi+np.pi
one_cycle=np.arange(0,1,1e-3)*2*np.pi
itf=np.empty_like(wl)



for i in range(len(wl)):
    #light from surface
    light_sur=sp.values[i]*R*np.sin(one_cycle+phase_diff.values[i])

    #light throught the 1st cellophane
    lp1=(((2*tc)%wl_c.values[i])/wl_c.values[i])*2*np.pi
    light1=sp.values[i]*R*T**2*np.sin(one_cycle+phase_diff.values[i]+lp1)

    #light throught the 2nd cellophane
    light2=sp.values[i]*R*T**2*np.sin(one_cycle+phase_diff.values[i]+lp1*2)

    check=(np.sin(one_cycle)+light_sur+light1+light2)**2
    itf[i]=np.amax(check)
plt.plot(wl,itf)
plt.show()





'''


c=c0/n2               #speed of light in glass[m/sec]
freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi
R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance

#x-axis calculation
depth=np.linspace(0,xmax*1e3,len(freq))
time=2*(n2*depth*1e-3)/c0

ref=np.sin(one_cycle) #reference light
#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

for i in range(1):
    for j in tqdm(range(len(freq))):
        wl_g=c/freq[j]*1e-12 #wavelength of incident wave[m](glass)
        wl_a=c0/freq[j]*1e-12

        phase_diff=(ta%wl_a)/wl_a*2*np.pi+np.pi

        #light from surface
        light_sur=R*np.sin(one_cycle+phase_diff)

        #light throught the 1st glass
        lp1=(((2*tg1)%wl_g)/wl_g)*2*np.pi
        light1=R*T**2*np.sin(one_cycle+phase_diff+lp1)

        #light throught the 2nd glass
        if tg2==0:
            light2=0
        else:
            lp2=((2*tg2)%wl_g)/wl_g*2*np.pi
            light2=R*T**4*np.sin(one_cycle+phase_diff+lp1+lp2)

        #light throught the 3rd glass
        if tg3==0:
            light3=0
        else:
            lp3=((2*(tg1+tg2+tg3))%wl_g)/wl_g*2*np.pi
            light3=T**4*R*np.sin(one_cycle+phase_diff+lp3)

        #light throught the 4th glass
        if tg4==0:
            light4=0
        else:
            lp4=((2*(tg1+tg2+tg3+tg4))%wl_g)/wl_g*2*np.pi
            light4=T**6*np.sin(one_cycle+phase_diff+lp4)
            if tg5!=0:
                light4*=R

        #light throught the 5th glass
        if tg5==0:
            light5=0
        else:
            lp5=((2*(tg1+tg2+tg3+tg4+tg5))%wl_g)/wl_g*2*np.pi
            light5=T**8*np.sin(one_cycle+phase_diff+lp5)    
        
        #plt.plot(one_cycle,ref,label='reference light')
        #plt.plot(one_cycle,light_sur,label='light from surface')
        #plt.plot(one_cycle,light1,label='light through the glass')
        #plt.xlabel('phase[rad]')
        #plt.legend()
        #plt.show()
        #print(freq[j])
        
        check=(ref+light_sur+light1+light2+light3+light4+light5)**2
        itf[j]=np.amax(check)-1
        itf_wf=itf*wf
    
    #plt.lot(freq,itf)
    #plt.xlim(190,191)
    #plt.xlabel('frequency[THz]')
    #plt.show()


    #inverse ft
    for j in tqdm(range(len(freq))):
        if j==0:
            result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
        else:
            result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    result/=len(freq)

    plt.plot(depth,abs(result))
plt.xlabel('Depth[mm]')
plt.ylabel('Intensity(arb. unit)')
#plt.xticks(np.arange(0,xmax*1e3,0.5))
plt.ylim(0,0.005)
plt.show()
'''