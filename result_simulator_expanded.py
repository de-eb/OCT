import numpy as np
import matplotlib.pyplot as plt

#model configulation
width=4  #width of glass[mm] <x-axis>
depth=5  #depth of glass[mm] <y-axis>
r=1      #radius of bubble in glass[mm]
circle_x=np.linspace(width/2-r,width/2+r,r*2*100)
circle_upper=np.sqrt(r**2-(circle_x-width/2)**2)+depth/2
circle_lower=-circle_upper+depth
'''
#model check drawing
plt.plot(circle_x,circle_upper)
plt.plot(circle_x,circle_lower)
plt.hlines(depth,0,width)
plt.vlines(width,0,depth)
plt.xlim(0,width+1)
plt.ylim(0,depth+1)
plt.show()
'''
x_axis=np.linspace(0,width,width*100)
partAC=[0,depth]
partB=[]
for i in range(len(circle_x)):
    partB.append([0,circle_lower[i],circle_upper[i],depth])
print(partB)
    


#constants
c0=299792458  #speed of light in vacuum[m/sec]
n1=1.0        #refractive index of air
n2=1.5        #refractive index of glass 
ta=150e-3       #thickness of air
fmin=189.7468 #minimum sweep frequency[THz]
fmax=203.2548 #maximum sweep frequency[THz]
fstep=1e-3  #sweep frequency step[THz]
xmax=4e-3
c=c0/n2               #speed of light in glass[m/sec]
freq=np.arange(fmin,fmax,fstep)
itf=np.empty_like(freq)
one_cycle=np.arange(0,1,1e-3)*2*np.pi
R=((n2-n1)/(n1+n2))**2 #reflectace
T=1-R                 #transmittance

#x-axis calculation
depth_axis=np.linspace(0,xmax*1e3,len(freq))
time=2*(n2*depth*1e-3)/c0

ref=np.sin(one_cycle) #reference light
#window function
x=np.linspace(0,1,len(freq))
wf=0.42-0.5*np.cos(2*np.pi*x)+0.08*np.cos(4*np.pi*x)

