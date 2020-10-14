import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import ifft

# Data loading
data = np.loadtxt('data/201009_6.csv', delimiter=',')
freq = data[:,0]*1e9 # frequency[GHz]
itf = data[:,1]  # interference spectra
ref = np.loadtxt('data/201009_ref2.csv', delimiter=',')[:,1]  # reference spectra
n=1.5 #refractive index
itf_BGremoved=itf-ref

# inverse fft
data=np.abs(np.fft.ifft(itf_BGremoved))

# x-axis calculation
time=1./(np.amax(freq)-np.amin(freq))*np.arange(0,len(freq))
depth=((time*3e8)/2*n)*1e3
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq)/2)]

plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.plot(depth,data)
plt.xlim(0,np.amax(depth))
plt.ylim(0,0.04)
plt.show()
