import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft

x=np.arange(0,1,0.001)
y=2*np.sin(2*np.pi*x)+3*np.sin(2*np.pi*2*x)+2.5*np.sin(2*np.pi*5*x)
result=np.abs(fft(y))

plt.plot(x,result)
plt.show()