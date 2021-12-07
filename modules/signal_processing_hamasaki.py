import numpy as np
from pycubicspline import Spline

class SignalProcessorHamasaki():
    """
    A class that packages various types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in vacuum [m/sec].

    def __init__(self,wavelength,n,depth_max,signal_length):
        """
        Initialization and preprocessing of parameters.

        Parameters
        ----------
        wavelength : `1d-ndarray`, required
            Wavelength axis[nm] The given spectra must be sampled evenly in wavelength space.
        n : `float`, required
            Refractive index of the sample .
        xmax : 'float', required
            maximum value of depth axis[mm]
        signal_length :  `float`, required
            Signal length.(3 is recomended)
            The calculation result always be periodic function. 
            This parameter controls the length of the cycle.
            The higher this parameter, the longer the period, but also the longer the time required for the calculation.

        """
        # Axis conversion for resampling
        self.__wl=wavelength
        self.__depth=np.linspace(0, depth_max, int(1e5))
        self.__time=2*(n*self.__depth*1e-3)/SignalProcessorHamasaki.c
        self.__freq=(SignalProcessorHamasaki.c/(self.__wl*1e9))*1e6
        self.__freq_fixed=np.linspace(np.amin(self.__freq)-1,np.amax(self.__freq)+1,int(len(self.__wl)*signal_length))
        #initialize data container
        self.__ref=None

    @property
    def depth(self):
        """ Horizontal axis after FFT (depth [m])
        """
        return self.__depth

    def resample(self,spectra):
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
        `pycubicspline.py`
        
        If pycubicspline.py isn't in the same directory, this program(siganl_processing_hamasaki.py) won't works.
        If you don't have the file, you can download it from https://github.com/AtsushiSakai/pycubicspline 
        """
        spline=Spline(np.flipud(self.__freq),np.flipud(spectra))
        itf_fixed=[spline.calc(i) for i in self.__freq_fixed]
        for i in range(len(itf_fixed)):
            if itf_fixed[i]==None:
                itf_fixed[i]=0
        return itf_fixed

    def set_reference(self,reference):
        """ Specify the reference spectra. This spectra will be used in later calculations.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.
        """
        self.__ref=self.resample(reference)

    def remove_background(self,spectra):
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
        return spectra-np.multiply(self.__ref,(np.amax(spectra)/np.amax(self.__ref)))

    def apply_inverse_ft(self,spectra):
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
                result=spectra[i]*np.sin(2*np.pi*self.__time*self.__freq_fixed[i]*1e12)
            else:
                result+=spectra[i]*np.sin(2*np.pi*self.__time*self.__freq_fixed[i]*1e12)
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
        itf=self.resample(interference)
        rmv=self.remove_background(itf)
        ascan=self.apply_inverse_ft(rmv)
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

    SigPro=SignalProcessorHamasaki(wl,1.4,0.2,3)
    depth,result=SigPro.generate_ascan(sp,bg)
    plt.plot(depth,result)
    plt.show()
