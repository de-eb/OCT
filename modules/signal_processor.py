import pandas as pd
import numpy as np
from scipy import special, interpolate


class SignalProcessor():
    """ A class that packages various types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in a vacuum [m/sec].

    def __init__(self, wavelength, n, alpha=1.5):
        """ Initialization and preprocessing of parameters.

        Parameters
        ----------
        wavelength : `1d-ndarray`, required
            Wavelength axis [nm]. The given spectra must be sampled evenly in wavelength space.
        n : `float`, required
            Refractive index of the sample.
        alpha : `float`
            Design factor of Kaiser window.
        """
        # Data containers
        self.__ref_fix = None

        # Axis conversion for resampling
        self.__wl = wavelength
        self.__ns = len(self.__wl)  # Number of samples after resampling
        i = np.arange(self.__ns)
        s = (self.__ns-1)/(self.__wl.max()-self.__wl.min()) * (1/(1/self.__wl.max()+i/(self.__ns-1)*(1/self.__wl.min()-1/self.__wl.max())) - self.__wl.min())
        self.wl_fix = self.__wl.min() + s*(self.__wl.max()-self.__wl.min())/(self.__ns-1)  # Fixed Wavelength
        
        # Generating window functions
        x = np.linspace(0, self.__ns, self.__ns)
        self.__window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
        
        # Axis conversion for FFT
        freq = SignalProcessor.c / (self.wl_fix*1e-9*n)
        fs = 2*freq.max()  # Nyquist frequency
        self.__nf = self.__ns * 2 # Number of samples after IFFT
        t = self.__nf / fs  # Maximum value of time axis after IFFT
        self.__depth = np.linspace(0, SignalProcessor.c*t/2, self.__ns)
        # depth = c*(1/(c/(wl_fix*n)))/(2*n)

    @property
    def depth(self):
        """ Horizontal axis after FFT (depth [m])
        """
        return self.__depth

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
        func = interpolate.interp1d(self.__wl, spectra, kind='cubic')
        return func(self.wl_fix)

    def remove_background(self, spectra):
        """ Removes the reference spectra from the interference spectra.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra. Normally, specify the interference spectra after resampling.

        Returns
        -------
        `1d-ndarray`
            Spectra after reference spectra removal.
        """
        return spectra/spectra.max() - self.__ref_fix/self.__ref_fix.max()
    
    def apply_window(self, spectra):
        """ Multiply the spectra by the window function.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra. (After removing the background.)

        Returns
        -------
        `1d-ndarray`
            Spectra after applying the window function.
        """
        return spectra*self.__window
    
    def apply_ifft(self, spectra):
        """ Apply IFFT to the spectra and convert it to time domain data (i.e. A-scan).

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra. (After applying the window function.)

        Returns
        -------
        `1d-ndarray`
            Data after IFFT.
        """
        magnitude = np.abs(np.fft.ifft(spectra, n=self.__nf, axis=0))
        return magnitude[:self.__ns]
    
    def set_reference(self, spectra):
        """ Specify the reference spectra. This spectra will be used in later calculations.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.
        """
        self.__ref_fix = self.resample(spectra)
    
    def generate_ascan(self, interference, reference):
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
        if self.__ref_fix is None:
            self.set_reference(reference)
        itf = self.resample(interference)
        rmv = self.remove_background(itf)
        wnd = self.apply_window(rmv)
        ascan = self.apply_ifft(wnd)
        return ascan


class DatasetHandler():
    """
    """

    def __init__(self, sheet, wavelength=None):
        """
        """
        self.__wl_fix = wavelength
        self.__n,self.__wl_n,self.__k,self.__wl_k,self.__alpha,self.__wl_alpha = None,None,None,None,None,None

        self.__df = pd.read_excel('modules/tools/optical_constants_dataset.xlsx', sheet_name=sheet, header=2, index_col=0)        
        for i in list(self.__df.columns):
            if i == 'n':
                self.__n, self.__wl_n = self.__get_data(i)
            elif i == 'k' or 'k ' in i:
                self.__k, self.__wl_k = self.__get_data(i)
            elif 'alpha' in i:
                self.__alpha, self.__wl_alpha = self.__get_data(i, normalize=True)
        print('Loaded the "{}" dataset.'.format(sheet))
    
    def __get_data(self, name, normalize=False):
        """
        """
        data = self.__df.loc[:, name].values
        wl = self.__df.iloc[:, self.__df.columns.get_loc(name)-1].values
        if normalize:
            data = data / data.max()
        if self.__wl_fix is not None:
            func = interpolate.interp1d(wl, data, kind='cubic')
            data = func(self.__wl_fix)
            wl = self.__wl_fix
        return data, wl

    @property
    def n(self) -> np.ndarray:
        """Refractive index against wavelength."""
        return self.__n
    
    @property
    def wl_n(self) -> np.ndarray:
        """Wavelength data corresponding to `self.n`."""
        return self.__wl_n
    
    @property
    def k(self) -> np.ndarray:
        """Extinction coefficient against wavelength."""
        return self.__k
    
    @property
    def wl_k(self) -> np.ndarray:
        """Wavelength data corresponding to `self.k`."""
        return self.__wl_k
    
    @property
    def alpha(self) -> np.ndarray:
        """Absorption coefficient against wavelength."""
        return self.__alpha
    
    @property
    def wl_alpha(self) -> np.ndarray:
        """Wavelength data corresponding to `self.alpha`."""
        return self.__wl_alpha


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter

    # Graph settings
    plt.rcParams['font.family'] ='sans-serif'
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams["xtick.minor.visible"] = True
    plt.rcParams["ytick.minor.visible"] = True
    plt.rcParams['xtick.major.width'] = 1.0
    plt.rcParams['ytick.major.width'] = 1.0
    plt.rcParams["xtick.minor.width"] = 0.5
    plt.rcParams["ytick.minor.width"] = 0.5
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.linewidth'] = 1.0

    st = 762  # Calculation range (Start)
    ed = 953  # Calculation range (End)

    # Data loading
    data = pd.read_csv('data/211116_1.csv', header=2, index_col=0)
    wl = data.values[st:ed,0]  # wavelength
    ref = data.values[st:ed,1]  # background spectra
    itf = data.values[st:ed,2]  # sample spectra

    # Signal processing
    sp = SignalProcessor(wl, 1.0)
    cellulose = DatasetHandler('Cellulose', wl)
    pet = DatasetHandler('PET', wl)
    # ascan = sp.generate_ascan(itf, ref)

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    # ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    # ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    # ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    # ax0_0, = ax0.plot(wl, itf, label='interference')
    # ax0_1, = ax0.plot(wl, ref, label='reference')
    # ax0.legend(borderaxespad=0.2)
    # ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
    # ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    # ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    # ax1_0, = ax1.plot(sp.depth*1e6, ascan, label='Numpy fft')
    # ax1.legend(borderaxespad=0.2)
    ax2 = fig.add_subplot(111, title='Dataset', xlabel='Wavelength [nm]', ylabel='alpha [-]')
    ax2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax2.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax2_0, = ax2.plot(pet.wl_alpha, pet.alpha, label='PET')
    ax2_1, = ax2.plot(cellulose.wl_alpha, cellulose.alpha, label='Cellulose')
    ax2.legend(borderaxespad=0.2)
    plt.show()
