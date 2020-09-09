import numpy as np
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plt


# 時系列のサンプルデータの作成
N = 40                      # データ数
T=10            # サンプリング幅
del_t= T/N   #  サンプリング間隔

del_w=2*np.pi/T # 離散フーリエ変換の振動数の間隔
#

# 離散点　生成
t = np.arange(0,T-del_t,del_t)
w=np.arange(2*np.pi/T, 2*np.pi*N/T, del_w)

#

f = np.exp(-(t-5)**2) # # サンプルデータを与える関数
#f=np.sin(2*np.pi*3*t)

#
g = fft(f)

g_real=np.real(g)
g_imag=np.imag(g)

#plot
plt.xlabel('w', fontsize=24)
plt.ylabel('g(w)', fontsize=24)

plt.plot(w,g_real,marker='o', markersize=4,label='Fourier transform: Real part')
plt.plot(w,g_imag,marker='o',markersize=4, label='Fourier transform: Imaginary part')

plt.legend(loc='best')

plt.show()


# パワースペクトルの表示

plt.plot(w,np.abs(g)**2,marker='o',markersize=4,label='|g(w)|^2')

plt.xlabel('w', fontsize=24)
plt.ylabel('Power spectrum |g(w)|^2', fontsize=24)
plt.legend(loc='best')

plt.show()


# 逆離散フーリエ変換

ff = ifft(g)
print(g)
plt.plot(t, np.real(ff), label='Fourier inverse transform: Real part')
plt.plot(t, np.imag(ff), label='Fourier inverse transform: Imaginary part')

plt.plot(t, f,'o',markersize=4,label='Raw data')


plt.xlabel('t', fontsize=24)
plt.ylabel('f(t)', fontsize=24)
plt.legend(loc='best')

plt.show()