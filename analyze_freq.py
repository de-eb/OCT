import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import ifft
    
# Data loading
data = np.loadtxt('data/200925_2.csv', delimiter=',')
freq = data[:,0]*1e9 # frequency[GHz]
itf = data[:,1]  # interference spectra
ref = np.loadtxt('data/200925_2_ref.csv', delimiter=',')[:,1]  # reference spectra
n=1.5 #refractive index
data_miss=np.loadtxt('data/200917_correct.csv',delimiter=',',encoding='utf-8_sig')#レーザー強度の波長依存性のデータ
miss=data_miss[:,1]#レーザー強度の波長依存性のデータ,光強度だけ
correction=miss/np.average(miss) #測定データからレーザー強度の波長依存性を取り除くための行列

# Background Subtraction
itf_BGremoved = itf - ref #interference spectra(background removed)
itf_BGremoved_corrected=itf_BGremoved*correction

# inverse fft
data=np.abs(np.fft.ifft(itf_BGremoved_corrected))
data2=np.abs(np.fft.ifft(itf_BGremoved))

# x-axis calculation
time=np.arange(0,len(freq))
timeband=1./(np.amax(freq)-np.amin(freq))#時間軸刻み幅
time=timeband*time #ここで[psec]
depth=((time*3e8)/2*n)*1e3
depth=depth-np.amin(depth)
depth=depth-depth[int(len(freq)/2)]


plt.xlabel("depth[mm]")
plt.ylabel("light intensity")
plt.plot(depth,data,label='corrected')
plt.plot(depth,data2,label='non-corrected')
plt.xlim(0,np.amax(depth))
plt.legend()
plt.show()
