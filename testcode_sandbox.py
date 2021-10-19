import numpy as np
import matplotlib.pyplot as plt
from numpy import fft 

if __name__=='__main__':
    f=1000
    rate=44100
    T=np.arange(0,0.01,1/rate)
    s=[]
    for t in T:
        v=np.sin(2*np.pi*f*t)+np.sin(2*np.pi*f*t*2)
        s.append(v)
    plt.plot(T,s)
    plt.xlabel('time')
    plt.ylabel('Gain')
    plt.show()

    fft_data=np.abs(np.fft.rfft(s))
    freqList=np.fft.rfftfreq(len(s),1.0/rate)
    plt.loglog(freqList,10*np.log(fft_data))
    #plt.plot(freqList,fft_data)
    plt.xlabel('frequency')
    plt.ylabel('power')
    plt.show()

    r=np.fft.irfft(fft_data,len(T))
    plt.plot(T,r)
    plt.xlabel('time')
    plt.ylabel('gain')
    plt.show()