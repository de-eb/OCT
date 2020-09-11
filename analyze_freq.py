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
time=1./freq
depth=((time*3e8)/2)*1e9
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq)/2)]


plt.xlabel("depth[nm]")
plt.ylabel("light intensity")
plt.plot(depth,data)
plt.show()
