import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

#model configulation
model_check_drawing=0
width=2 #width of glass[mm] <x-axis>
depth=3  #depth of glass[mm] <y-axis>
r=1    #radius of bubble in glass[mm]
split=25 #[mm^-1]
depth_depression=0 #depth of depresshon[mm]
circle_x=np.linspace(width/2-r,width/2+r,int(r*2*split))
depression_x=np.linspace(0,1,len(circle_x))
depression=depth_depression*np.sin(2*np.pi*depression_x)+depth_depression
depth+=depth_depression
circle_upper=np.sqrt(abs(r**2-(circle_x-width/2)**2))+depth/2
circle_lower=-circle_upper+depth
'''
for i in range(len(circle_x)):
    if depression[i]>=depth_depression:
        depression[i]=depth_depression+depth_depression
    else:
        depression[i]=-depth_depression+depth_depression
'''

for i in range(len(circle_x)):
    circle_lower[i]=0.1
    circle_upper[i]=0.1+9.82e-3
depth=0.3

#constants
c0=299792458  #speed of light in vacuum[m/sec]
n0=1          #refractive index of air(normal=1)
n1=1.5        #refractive index of surrounding substance
n2=1.5        #refractive index of circle-shaped substance  
ta=150e-3     #thickness of air
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2548 #maximum sweep frequency[THz]
fstep=1e-3    #sweep frequency step[THz]
add_noise=0

#calculation based on constants
xmax=depth*1.2*1e-3 #x-axis length[m]
c1=c0/n1            #speed of light in surrounding substance[m/sec]
c2=c0/n2            #speed of light in circle-chaped substance
freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi
noise=np.empty_like(freq)
for i in range(len(noise)):
    noise[i]=0

R1=((n1-n0)/(n1+n0))**2 #refrectance of surface
T1=1-R1                  #transmittance of surface
R2=((n2-n1)/(n1+n2))**2 #reflectace of circle
T2=1-R2                 #transmittance  of circle

R2=R1
T2=T1

#x-axis calculation
depth_axis=np.linspace(0,xmax*1e3,len(freq))
time=2*(n1*depth_axis*1e-3)/c0

ref=np.sin(one_cycle) #reference light
#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

x_axis=np.linspace(0,width,int(width*split))

partAC=[depth_depression*1e-3,depth*1e-3]
partB=[]
for i in range(len(circle_x)):
    partB.append([float((depression[i])*1e-3),float(circle_lower[i]*1e-3),float(circle_upper[i]*1e-3),float(depth*1e-3)])

#model check drawing
if model_check_drawing:
    plt.plot(circle_x,circle_upper)
    plt.plot(circle_x,circle_lower)
    plt.plot(circle_x,depression)
    plt.hlines(depth,0,width)
    plt.hlines(depth_depression,0,width/2-r,)
    plt.hlines(depth_depression,width/2+r,width)
    plt.vlines(width,depth_depression,depth)
    plt.xlim(0,width*1.2)
    plt.ylim(np.amin(depression),depth*1.2)
    plt.xlabel('width[mm]')
    plt.ylabel('depth[mm]')
    plt.show()

for i in tqdm(range(len(x_axis))):
    if add_noise:
        for k in range(len(noise)):
            noise[k]=np.random.randint(-9,9)*1e-2
    for j in range(len(freq)):
        wl_a=c0/freq[j]*1e-12   #wavelenght of incident wave[m](air)
        wl_g1=c1/freq[j]*1e-12    #wavelength of incident wave[m](surrounding substance)
        wl_g2=c2/freq[j]*1e-12   #wavelength of incident wave[m](circle-shaped substance)
        
        light1=light2=light3=0 #initialize each light

        if i<=(width/2-r)*split or i>=(width/2+r)*split:
            phase_diff=((ta+partAC[0]*2)%wl_a)/wl_a*2*np.pi+np.pi
            lp1=((2*(partAC[1]-partAC[0]))%wl_g1)/wl_g1*2*np.pi
            light1=R1*T1**2*np.sin(one_cycle+phase_diff+lp1)

        else:
            phase_diff=((ta+2*partB[int(i-(width/2-r)*split)-1][0])%wl_a)/wl_a*2*np.pi+np.pi
            for k in range(3):
                if k==0:
                    lp1=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split-1)][k])%wl_g1)/wl_g1*2*np.pi
                    light1=R2*T1**2*np.sin(one_cycle+phase_diff+lp1)
                elif k==1:
                    lp2=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split)-1][k])%wl_g2)/wl_g2*2*np.pi
                    light2=R2*T1**2*T2**2*np.sin(one_cycle+phase_diff+lp1+lp2)
                elif k==2:
                    lp3=(2*(partB[int(i-(width/2-r)*split)-1][k+1]-partB[int(i-(width/2-r)*split)-1][k])%wl_g1)/wl_g1*2*np.pi
                    light3=R1*T1**2*T2**4*np.sin(one_cycle+phase_diff+lp1+lp2+lp3)
        
        #light from surface
        light_sur=R1*np.sin(one_cycle+phase_diff)
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
        itf_wf=(itf+noise)*wf
    '''
    #graph check(interference)
    if i==len(x_axis)/2:
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
    
    
    #graph check(1d result)
    plt.plot(depth_axis,abs(result))
    plt.xlabel('Depth [mm]',fontsize=16)
    plt.ylabel('Intensity [arb. unit]',fontsize=16)
    #plt.ylim(0,0.01)
    #plt.xticks(fontsize=16)
    #plt.yticks(fontsize=16)
    plt.xlim(0.08,0.13)
    plt.ylim(0,0.001)
    plt.show()

    if i==0:
        result_map=abs(result)
    else:
        result_map=np.vstack((result_map,abs(result)))


plt.figure()
plt.imshow(result_map,cmap='jet',extent=[0,np.amax(depth_axis),0,width],vmin=0,vmax=np.amax(result_map))
plt.colorbar()
plt.ylabel('Width [mm]',fontsize=18)
plt.xlabel('Depth [mm]',fontsize=18)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.show()