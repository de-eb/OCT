import numpy as np
import matplotlib.pyplot as plt

def inverse_ft_plot(freq,itf,xmax,n):
    depth_axis=np.linspace(0,xmax*1e3,int(1e5))
    time=2*(n*depth_axis*1e-3)/299792458

    for i in range(len(freq)):
        if i==0:
            result=itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        else:
            result+=itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
    result/=len(freq)
    
    return depth_axis,abs(result)