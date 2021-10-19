import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

#model configulation
width=2 #width of glass[mm] <x-axis>
depth=3 #depth of glass[mm] <y-axis>
r=0.5     #radius of bubble in glass[mm]
split=50 #[mm^-1]
circle_x=np.linspace(width/2-r,width/2+r,int(r*2*split))
circle_upper=np.sqrt(abs(r**2-(circle_x-width/2)**2))+depth/2
circle_lower=-circle_upper+depth
'''
#model check drawing
plt.plot(circle_x,circle_upper)
plt.plot(circle_x,circle_lower)
plt.hlines(depth,0,width)
plt.vlines(width,0,depth)
plt.xlim(0,width*1.2)
plt.ylim(0,depth*1.2)
plt.xlabel('width[mm]')
plt.ylabel('depth[mm]')
plt.show()
'''
#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1        #refractive index of air
n2=1.5        #refractive index of glass 
ta=150e-3       #thickness of air
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2548 #maximum sweep frequency[THz]
fstep=2e-3  #sweep frequency step[THz]
xmax=depth*1.2*1e-3 #x-axis length[m]
c=c0/n2               #speed of light in glass[m/sec]
c1=c0/n1            #speed of light in air
freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi+np.pi
R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance
#x-axis calculation
depth_axis=np.linspace(0,xmax*1e3,len(freq))
time=2*(n2*depth_axis*1e-3)/c0

ref=np.sin(one_cycle) #reference light
#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

x_axis=np.linspace(0,width,int(width*split))

partAC=[0,depth*1e-3]
partB=[]
for i in range(len(circle_x)):
    partB.append([0,float(circle_lower[i]*1e-3),float(circle_upper[i]*1e-3),float(depth*1e-3)])

for i in tqdm(range(len(x_axis))):
    for j in range(len(freq)):
        wl_g=c/freq[j]*1e-12    #wavelength of incident wave[m](glass)
        wl_a=c1/freq[j]*1e-12   #wavelength of incident wave[m](air)
        
        phase_diff=(ta%wl_a)/wl_a*2*np.pi+np.pi
        light1=light2=light3=0

        #light from surface
        light_sur=np.sin(one_cycle+phase_diff)

        if i<=(width/2-r)*split or i>=(width/2+r)*split:
            frag=0
            lp1=((2*(partAC[1]-partAC[0]))%wl_g)/wl_g*2*np.pi
            light1=R*np.sin(one_cycle+phase_diff+lp1)

        else:
            frag=1
            for k in range(3):
                if k==0:
                    lp1=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split-1)][k])%wl_g)/wl_g*2*np.pi
                    light1=R*np.sin(one_cycle+phase_diff+lp1)
                elif k==1:
                    lp2=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split)-1][k])%wl_a)/wl_a*2*np.pi
                    light2=R*T**2*np.sin(one_cycle+phase_diff+lp1+lp2)
                elif k==2:
                    lp3=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split)-1][k])%wl_g)/wl_g*2*np.pi
                    light3=R*T**4*np.sin(one_cycle+phase_diff+lp1+lp2+lp3)
        '''
        #graph check(phase relationship)
        plt.plot(one_cycle,ref,label='referencelight')
        plt.plot(one_cycle,light_sur,label='light from surface')
        plt.plot(one_cycle,light1,label='light through the glass')
        plt.xlabel('phase[rad]')
        plt.legend()
        plt.show()
        '''
        check=(ref+light_sur+light1+light2+light3)**2
        itf[j]=np.amax(check)-1
        itf_wf=itf*wf
    '''
    #graph check(interference)
    if i%20==0:
        plt.plot(freq,itf)
        plt.xlim(190,191)
        plt.xlabel('frequency[THz]')
        plt.show()
    '''
    # inverse ft
    for j in range(len(freq)):
        if j==0:
            result=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
        else:
            result+=itf_wf[j]*np.sin(2*np.pi*time*freq[j]*1e12)
    result/=len(freq)
    '''
    if i%20==0:
        #graph check(result)
        plt.plot(depth_axis,abs(result))
        plt.xlabel('depth[mm]')
        plt.ylabel('signal intensity(arb. unit)')
        plt.show()
    '''
    if i==0:
        result_map=abs(result)
    else:
        result_map=np.vstack((result_map,abs(result)))

plt.figure()
plt.imshow(result_map,cmap='jet',extent=[0,depth*1.2,0,width],vmin=0,vmax=np.amax(result_map)/30)
plt.colorbar()
plt.ylabel('width[mm]')
plt.xlabel('depth[mm]')
plt.show()