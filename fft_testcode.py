import numpy as np
from scipy.fftpack import fft
import matplotlib.pyplot as plt

N=2**20    #データ数
dt=0.0001  #データ幅
f1,f2=5,8  #周波数
A1,A2=5,0  #振幅
p1,p2=0,0  #位相

t=np.arange(0,N*dt,dt)
freq=np.linspace(0,1.0/dt,N)

y=A1*np.sin(2*np.pi*f1*t+p1)+A2*np.sin(2*np.pi*f2*t+p2)

yf=fft(y)/(N/2)

plt.figure(2)
plt.subplot(211)
plt.plot(t,y)
plt.xlim(0,1)
plt.xlabel("time")
plt.ylabel("amplitude")

plt.subplot(212)
plt.plot(freq,np.abs(yf))
plt.xlim(0,10)
plt.ylim(0,5)
plt.xlabel("frequency")
plt.ylabel("amplitude")
plt.tight_layout()
plt.show()