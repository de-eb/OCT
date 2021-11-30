import numpy as np
from numpy.lib.type_check import asscalar
from pycubicspline import *

class SignalProcessor_hamasaki():
    """
    A class that packages various types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in vacuum [m/sec].

    def __init__(self,wl,n,xmax,sl):
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
        sl :  `float`, required
            Signal length.(3 is recomended)
            The calculation result always be periodic function. 
            This parameter controls the length of the cycle.
            The higher this parameter, the longer the period, but also the longer the time required for the calculation.

        """
        # Axis conversion for resampling
        self.__wl=wl
        self.__depth=np.linspace(0, xmax, int(1e5))
        self.__time=2*(n*self.__depth*1e-3)/SignalProcessor_hamasaki.c
        self.__freq=(SignalProcessor_hamasaki.c/(self.__wl*1e9))*1e6
        self.__freq_fixed=np.linspace(np.amin(self.__freq)-1,np.amax(self.__freq)+1,int(len(self.__wl)*sl))
        #initialize data container
        self.__ref=None

    @property
    def depth(self):
        """ Horizontal axis after FFT (depth [m])
        """
        return self.__depth

    def Resampling(self,sp):
        """Resampling function for OCT.
    
        Parameters
        ----------
        sp : `1d-ndarray`
            measured interference data[arb. unit]
        
        Returns
        -------
        itf_fixed : `1d-ndarray`
            Spectra resampled evenly in the frequency space.
        
        Requirement
        -------
        pycubicspline.py (from pycubicspline import *)
        """
        spline=Spline(np.flipud(self.__freq),np.flipud(sp))
        itf_fixed=[spline.calc(i) for i in self.__freq_fixed]
        for i in range(len(itf_fixed)):
            if itf_fixed[i]==None:
                itf_fixed[i]=0
        return itf_fixed

    def set_reference(self,ref):
        """ Specify the reference spectra. This spectra will be used in later calculations.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.
        """
        self.__ref=self.Resampling(ref)

    def BGsubtraction(self,sp):
        """Subtract reference light from interference light.
    
        Parameters
        ----------
        sp : `1d-ndarray`, required
            Spectra. Normally, specify the interference spectra after resampling.

        
        Return
        -------
        `1d-ndarray`
            interference light removed background[arb. unit]
        """
        return sp-np.multiply(self.__ref,(np.amax(sp)/np.amax(self.__ref)))

    def inverse_ft(self,sp):
        """Apply inverse ft to the spectra and convert it to distance data

        Parameters
        ----------
        sp : `1d-ndarray`, required
            spectra(After applying resampling)

        Returns
        ----------
        `1d-array`
            Data after IFFT
        
        """
        for  i in range(len(self.__freq_fixed)):
            if i==0:
                result=sp[i]*np.sin(2*np.pi*self.__time*self.__freq_fixed[i]*1e12)
            else:
                result+=sp[i]*np.sin(2*np.pi*self.__time*self.__freq_fixed[i]*1e12)
        result/=np.amax(result)
        return abs(result)

    def generate_ascan(self,interference,reference):
        """ Performs a series of signal processing in one step.

        Parameters
        ----------
        interference : `1d-ndarray`, required
            Spectra of interference light only, sampled evenly in wavelength space.
        reference : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.

        Returns
        -------
        ascan : `1d-ndarray`
            Light intensity data in the time domain (i.e. A-scan).
            The corresponding horizontal axis data (depth) can be obtained with `self.depth`.
        """
        if self.__ref==None:
            self.set_reference(reference)
        itf=self.Resampling(interference)
        rmv=self.BGsubtraction(itf)
        ascan=self.inverse_ft(rmv)
        return self.__depth,ascan

if __name__=="__main__":
    import pandas as pd
    import matplotlib.pyplot as plt

    st = 333
    ed = 533
    name=['wl','bg','sp']
    data=pd.read_csv('data/211103_0.csv', header=3, index_col=0,names=name)
    wl=data.loc[st:ed,'wl'] # Wavelength
    bg=data.loc[st:ed,'bg'] # Background spectra
    sp=data.loc[st:ed,'sp'] # Sample spectra

    SigPro=SignalProcessor_hamasaki(wl,1.4,0.2,3)
    depth,result=SigPro.generate_ascan(sp,bg)
    plt.plot(depth,result)
    plt.show()


'''
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

    freq=(299792458/(wl*1e9))*1e6
    spline=Spline(np.flipud(freq),np.flipud(itf))
    freq_fixed=np.linspace(np.amin(freq)-1,np.amax(freq)+1,len(wl)*3)
    itf_fixed=[spline.calc(i) for i in freq_fixed]
    for i in range(len(itf_fixed)):
        if itf_fixed[i]==None:
            itf_fixed[i]=0
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
    return freq_fixed,itf_fixed

def inverse_ft(freq, itf, xmax, n):
    depth = np.linspace(0, xmax, int(1e5))
    time = 2*(n*depth*1e-3)/299792458
    for i in range(int(len(freq))):
        if i==0:
            result = itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        else:
            result += itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
    result /= np.amax(result)
    return depth, abs(result)
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

'''
'''
クラスの中のinitには一度しか計算が必要ないものを入れる
例・窓関数・深さ方向軸・屈折率の記録・参照光のデータ
リアルタイム計測に向けて計算は必要最小限に抑える、何度計算しても同じになるものは入れない
'''