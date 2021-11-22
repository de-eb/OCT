import numpy as np
from pycubicspline import *

class SignalProcessor_hamasaki():
    """
    A class that packages variou types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in a vacuum [m/sec].

    def __init__(self,wl,n,xmax):
        """
        Initialization and preprocessing of parameters.

        Parameters
        ----------
        wl : `1d-ndarray`, required
            Wavelength axis[nm] The given spectra must be sampled evenly in wavelength space.
        n : `float`, required
            Refractive index of the sample .
        xmax : 'float', required
            maximum value of depth axis[mm]
        
        """
        # Axis conversion for resampling
        self.__wl=wl
        self.__depth=np.linspace(0, xmax, int(1e5))
        self.__time=2*(n*depth*1e-3)/SignalProcessor_hamasaki.c
        freqmin=(SignalProcessor_hamasaki.c/(1e9*np.amax(self.__wl)))*1e6+1
        freqmax=(SignalProcessor_hamasaki.c/(1e9*np.amin(self.__wl)))*1e6-1
        self.__freq=np.linspace(freqmin,freqmax,len(self.__wl))
        







def BGsubtraction(sp,bg):
    """Subtract reference light from interference light.
    
        Parameters
        ----------
        sp : `ndarray`
            interference light[arb. unit]
        bg : `ndarray`
            reference light[arb. unit]
        
        Return
        -------
        itf :`ndarray`
            interference light removed background[arb. unit]

    """
    itf=sp-bg*(np.amax(sp)/np.amax(bg))
    return itf

def Resampling(wl,itf):
    """Resampling function for OCT.
    
        Parameters
        ----------
        wl : `ndarray`
            wavelength data[nm]
        itf : `ndarray`
            measured interference data[arb. unit]
        
        Returns
        -------
        freq_fixed : `ndarray`
            calculated frequency data[THz] 
        itf_fixed : `ndarray`
            fixed interference data[arb. unit]
        
        Requirement
        -------
        pycubicspline.py (from pycubicspline import *)
    """
    freq=(299792458/(wl*1e9))*1e6
    spline=Spline(np.flipud(freq),np.flipud(itf))
    freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,len(wl)*3)
    itf_fixed=[spline.calc(i) for i in freq_fixed]
    for i in range(len(itf_fixed)):
        if itf_fixed[i]==None:
            itf_fixed[i]=0
    return freq_fixed,itf_fixed

def inverse_ft(freq, itf, xmax, n):
    """Inverse Fourier transform function for OCT.
    
        Parameters
        ----------
        freq : `ndarray`
            frequency data[THz]
        itf : `ndarray`
            measured interference data[arb. unit]
        xmax : `float`
            maximum value of depth axis[mm]
        n : `float`
            refractive index of sample
        
        Returns
        -------
        depth_axis : `ndarray`
            calculated depth axis[mm]
        result : `ndarray`
            transformed data[arb. unit]
    """
    depth = np.linspace(0, xmax, int(1e5))
    time = 2*(n*depth*1e-3)/299792458
    for i in range(int(len(freq))):
        if i==0:
            result = itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        else:
            result += itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
    result /= np.amax(result)
    return depth, abs(result)

if __name__ == "__main__":
    import pandas as pd
    import matplotlib.pyplot as plt

    st = 333
    ed = 533
    name=['wl','bg','sp']
    data=pd.read_csv('data/211103_0.csv', header=3, index_col=0,names=name)
    wl=data.loc[st:ed,'wl'] # Wavelength
    bg=data.loc[st:ed,'bg'] # Background spectra
    sp=data.loc[st:ed,'sp'] # Sample spectra

    itf=BGsubtraction(sp,bg)
    freq_fixed,itf_fixed=Resampling(wl,itf)
    depth,result=inverse_ft(freq_fixed,itf_fixed,0.2,1.4)

    plt.plot(depth,result)
    plt.show()

    '''クラスの中のinitには一度しか計算が必要ないものを入れる
    例・窓関数・深さ方向軸・屈折率の記録・参照光のデータ
    リアルタイム計測に向けて計算は必要最小限に抑える、何度計算しても同じになるものは入れない
    '''