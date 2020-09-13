import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.fftpack import ifft
    
# Data loading
data = np.loadtxt('data/200908_0.csv', delimiter=',')
freq = data[:,0]*1e9 # frequency[GHz]
itf = data[:,1]  # interference spectra
ref = np.loadtxt('data/200908_0_ref.csv', delimiter=',')[:,1]  # reference spectra

# Background Subtraction
itf_BGremoved = itf - ref #interference spectra(background removed)

# inverse fft
data=np.abs(np.fft.ifft(itf_BGremoved))

# x-axis calculation
time=np.arange(0,len(freq))
timeband=1./(np.amax(freq)-np.amin(freq))#時間軸刻み幅
time=timeband*time #ここで[psec]
depth=((time*3e8)/2)*1e3
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq)/2)]


plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.plot(depth,data)
plt.xlim(0,np.amax(depth))
plt.show()
