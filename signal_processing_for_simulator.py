import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import ifft

# Data loading
data1 = np.loadtxt('data/201021_simulated_0.1mm.csv', delimiter=',',encoding='utf-8_sig')
data2 = np.loadtxt('data/201019_simulated_0.5mm.csv', delimiter=',',encoding='utf-8_sig')
data3 = np.loadtxt('data/201019_simulated_1mm.csv', delimiter=',',encoding='utf-8_sig')
data4 = np.loadtxt('data/201021_simulated_2mm.csv', delimiter=',',encoding='utf-8_sig')
freq1 = data1[:,0]*1e9 # frequency[GHz]
itf1 = data1[:,1]  # interference spectra
freq2 = data2[:,0]*1e9
itf2 = data2[:,1]
freq3 = data3[:,0]*1e9
itf3 = data3[:,1]
freq4 = data4[:,0]*1e9
itf4 = data4[:,1]
n=1.5

# inverse fft
result1=np.abs(np.fft.ifft(itf1))
result2=np.abs(np.fft.ifft(itf2))
result3=np.abs(np.fft.ifft(itf3))
result4=np.abs(np.fft.ifft(itf4))

# x-axis calculation
time=1./(np.amax(freq1)-np.amin(freq1))*np.arange(0,len(freq1))
depth=((time*3e8)/2*n)*1e3
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq1)/2)]

plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.plot(depth,result1,label='0.1mm')
plt.plot(depth,result2,label='0.5mm')
plt.plot(depth,result3,label='1mm')
plt.plot(depth,result4,label='2mm')
plt.xlim(0,np.amax(depth))
plt.ylim(0,50)
plt.legend()
plt.show()