import numpy as np
from scipy import interpolate
from tqdm import tqdm

class SignalProcessorHamasaki():
    """
    A class that packages various types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in vacuum [m/sec].

    def __init__(self,wavelength,n,depth_max,resolution,signal_length=3):
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
        resolution : `int`
            Resolution of calculation result.
            The larger the value, the sharper the graph,but the calculation time.
        signal_length :  `float`
            Signal length.
            The calculation result always be periodic function. 
            This parameter controls the length of the cycle.
            The higher this parameter, the longer the period, but also the longer the time required for the calculation.

        """
        # Axis conversion for resampling
        self.__wl=wavelength
        self.__res=int(resolution)
        self.__depth=np.linspace(0, depth_max, self.__res)
        self.__time=2*(n*self.__depth*1e-3)/SignalProcessorHamasaki.c
        self.__freq=(SignalProcessorHamasaki.c/(self.__wl*1e9))*1e6
        self.__freq_fixed=np.linspace(np.amin(self.__freq),np.amax(self.__freq),int(len(self.__wl)*signal_length))
        self.__freq_dataset=self.__prepare_sinusoid(self.__freq_fixed)
        #initialize data container
        self.__ref=None

    @property
    def depth(self):
        """ Horizontal axis after FFT (depth [mm])
        """
        return self.__depth

    def __prepare_sinusoid(self, freq_fixed):
        """To speed up the calculation, this function calculates the sine wave needed for signal processing in advance.

        Parameter
        ----------
        freq_fixed : `1d-ndarray`, required
            Use equal width for each value, not the inverse of wavelength axis.
        
        Return
        ----------
        freq_dataset : `2d-ndarray`
            Calculated sine wave data set. If this array is referenced when using apply_inverse_ft function, processing can be sped up.
        """
        freq_dataset=np.zeros((len(freq_fixed),len(self.__time)))
        for i in range(len(freq_fixed)):
            freq_dataset[i]=np.sin(2*np.pi*self.__time*self.__freq_fixed[i]*1e12)
        return freq_dataset

    def resample(self, spectra):
        """ Resamples the spectra.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra sampled evenly in the wavelength space.
        Returns
        -------
        `1d-ndarray`
            Spectra resampled evenly in the frequency space.
        """
        func = interpolate.interp1d(self.__freq, spectra, kind='cubic')
        return func(self.__freq_fixed)

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
        spectra : `1d-ndarray`, required
            spectra(After applying resampling)

        Return
        ----------
        `1d-array`
            Data after IFFT
        
        """
        result=np.zeros_like(self.__depth)
        for i in range(len(spectra)):
            result+=spectra[i]*self.__freq_dataset[i]
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
        
        Return
        -------
        ascan : `1d-ndarray`
            Light intensity data in the time domain (i.e. A-scan).
            The corresponding horizontal axis data (depth) can be obtained with `self.depth`.
        """
        if self.__ref is None:
            self.set_reference(reference)
        itf=self.resample(interference)
        rmv=self.remove_background(itf)
        ascan=self.apply_inverse_ft(rmv)
        return ascan
    
    def generate_bscan(self,interference,reference):
        """Generate a B-scan by calling generate_ascan function multiple times.

        Parameters
        ----------
        intereference : `2d-ndarray`, required
            Spectra of interference light only, sampled evenly in wavelength space.
         reference : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.           

        Return
        ----------
        bscan : `2d-ndarray`
            Light intensity data in the time domain(i.e. B-scan)
            The corresponding horizontal axis data(depth) can be obtained with `self.depth`.      
        """
        bscan=np.zeros((len(interference),self.__res))
        print("Generating B-scan...")
        for i in tqdm(range(len(interference))):
            bscan[i]=self.generate_ascan(interference[i], reference)
        return bscan
    
    def generate_cscan(self, interference,reference):
        """Generate a C-scan by calling generate_ascan function multiple times.

        Parameters
        ----------
        intereference : `3d-ndarray`, required
            Spectra of interference light only, sampled evenly in wavelength space.
         reference : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.           

        Return
        ----------
        bscan : `3d-ndarray`
            Light intensity data in the time domain(i.e. C-scan)
            The corresponding horizontal axis data(depth) can be obtained with `self.depth`.      
        """
        cscan=np.zeros((len(interference),len(interference[0]),self.__res))
        print('Generating C-scan...')
        for i in tqdm(range(len(interference))):
            for j in range(len(interference[i])):
                cscan=self.generate_ascan(interference[i][j],reference)
        return cscan

#Please note that following 2 function is excluded from SignalProcessorHamasaki class, 
#since there are cases the the SignalProcessorHamasaki class is not needed as long as these function is called.
def generate_cross_section(cscan, target, depth):
    """Generates a cross-sectional view from c-scan data at a specified depth in a plane perpendicular to the optical axis direction.
    
    Parameters
    ----------
    cscan : `3d-ndarray`, required
        C-scan data calculated by generate_cscan function.
    target : `float` ,required
        Depth to generate cross-sectional view[μm].
    depth : `1d-ndarray`, required
        The corresponding horizontal axis data to C-scan.

    Return
    ----------
    cross_section : `2d-ndarray`
        Generated cross-sectional view of C-csan.
    """
    #find index to generate cross-sectional view
    target_mm = target*1e-3
    if np.amax(depth)<target_mm or np.amin(depth)>target_mm:
        print("Error:Target is not included in depth array. Returned depth[0].")
        index = 0
    else:
        for i in range(len(depth)):
            if depth[i]>=target_mm:
                index=i
                break

    #generate cross-sectional view
    cross_section=np.zeros((len(cscan),len(cscan[0])))
    for i in range(len(cscan)):
        for j in range(len(cscan[i])):
            cross_section[i][j]=cscan[i][j][index]
    return cross_section

def calculate_absorbance(transmittion,incidence):
    """Calculate tranmittance based on the incident and transmitted light.
    Parameters
    ----------
    transmittion : `1d-ndarray`, required
        Spectrum of the light source used to measure transmittance
    incidence : `1d-ndarray`, required
        Spectrum of light passing through the sample
    
    Return
    ----------
    absorbance : `1d-ndarray`
        calculated absorbance data 
    """
    with np.errstate(divide='ignore',invalid='ignore'):
        absorbance=np.log10(transmittion/incidence)*(-1)
    for i in range(len(absorbance)):
        if np.isinf(absorbance[i]):
            absorbance[i]=np.nan
    return absorbance

if __name__=="__main__":
     import matplotlib.pyplot as plt
     import pandas as pd

     st = 1664
     ed = 2491
     name=['wl','sp']
     data_ref=pd.read_csv('data/220608_0.csv', header=3, index_col=0,names=name)
     data_sp0=pd.read_csv('data/220613_1.csv',header=3, index_col=0,names=name)
     #data_sp1=pd.read_csv('data/220608_2.csv',header=3, index_col=0,names=name)
     #data_sp2=pd.read_csv('data/220608_3.csv',header=3, index_col=0,names=name)
    
     wl=data_ref.loc[st:ed,'wl'] # Wavelength
     bg=data_ref.loc[st:ed,'sp'] # Background spectra
     sp0=data_sp0.loc[st:ed,'sp'] # Sample spectra
     #sp1=data_sp1.loc[st:ed,'sp']
     #sp2=data_sp2.loc[st:ed,'sp']

     SigPro=SignalProcessorHamasaki(wavelength=wl,n=1.5,depth_max=0.4,resolution=20000)
     result0=SigPro.generate_ascan(sp0,bg)
     #result1=SigPro.generate_ascan(sp1,bg)
     #result2=SigPro.generate_ascan(sp2,bg)
     depth=SigPro.depth*1e3

     plt.plot(depth,result0)
     #plt.plot(depth,result1,label='cover glass + 1 layer of cellophane')
     #plt.plot(depth,result2,label='cover glass + 2 layers of cellophane')
     plt.xlabel('depth[mm]',fontsize=17)
     plt.ylabel('intensity[arb. unit]',fontsize=17)
     plt.legend()
     plt.xlim(0,np.amax(depth))
     plt.ylim(0,1)
     plt.xticks(fontsize=15)
     plt.yticks(fontsize=15)
     plt.show()