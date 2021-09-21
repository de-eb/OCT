import numpy as np
import pandas as pd
from scipy import special, interpolate
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


class SignalProcessor():
    """
    A class that packages various types of signal processing for OCT.
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
        self.reference = None

        # Axis conversion for resampling
        self.wl = wavelength
        self.ns = len(self.wl)  # Number of samples after resampling
        i = np.arange(self.ns)
        s = (self.ns-1)/(self.wl.max()-self.wl.min()) * (1/(1/self.wl.max()+i/(self.ns-1)*(1/self.wl.min()-1/self.wl.max())) - self.wl.min())
        self.wl_fix = self.wl.min() + s*(self.wl.max()-self.wl.min())/(self.ns-1)  # Fixed Wavelength
        
        # Generating window functions
        x = np.linspace(0, self.ns, self.ns)
        # self.window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
        self.window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
        
        # Axis conversion for FFT
        freq = SignalProcessor.c / (self.wl_fix*1e-9*n)
        fs = 2*freq.max()  # Nyquist frequency
        self.nf = self.ns * 2 # Number of samples after IFFT
        t = self.nf / fs  # Maximum value of time axis after IFFT
        self.depth = np.linspace(0, SignalProcessor.c*t/2, self.ns)
        # depth = c*(1/(c/(wl_fix*n)))/(2*n)

    def resample(self, spectra):
        """
        """
        func = interpolate.interp1d(self.wl, spectra, kind='cubic')
        return func(self.wl_fix)

    def remove_background(self, spectra):
        """
        """
        return spectra/spectra.max() - self.reference/self.reference.max()
    
    def apply_window(self, spectra):
        """
        """
        return spectra*self.window
    
    def apply_ifft(self, spectra):
        """
        """
        magnitude = np.abs(np.fft.ifft(spectra, n=self.nf, axis=0))
        return magnitude[self.ns:]
    
    def set_reference(self, spectra):
        """
        """
        self.reference = self.resample(spectra)
    
    def get_ascan(self, interference, reference):
        """
        """
        if self.reference is None:
            self.set_reference(reference)
        itf = self.resample(interference)
        rmv = self.remove_background(itf)
        wnd = self.apply_window(rmv)
        ascan = self.apply_ifft(wnd)
        return ascan
    
    def remove_autocorrelation(self, ascan0, ascan1):
        """
        """
        return np.abs(self.remove_background(ascan0, ascan1))

    def inverse_ft(freq, itf, xmax, n):
        """Inverse Fourier transform function for oct.
        
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
        depth_axis = np.linspace(0, xmax, int(1e5))
        time = 2*(n*depth_axis*1e-3)/c
        for i in range(len(freq)):
            if i==0:
                result = itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
            else:
                result += itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        result /= len(freq)
        return depth_axis, abs(result)


if __name__ == "__main__":

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

    st = 762  # Calculation range (Start) of spectrum [nm]
    ed = 953  # Calculation range (End) of spectrum [nm]

    # Data loading
    data = pd.read_csv('data/210903_1.csv', header=2, index_col=0)
    wl = data.values[st:ed,0]  # wavelength
    ref = data.values[st:ed,1]  # background spectra
    itf = data.values[st:ed,2]  # sample spectra

    # Signal processing
    sp = SignalProcessor(wl, 1.46)  # cellulose = 1.46
    ascan = sp.get_ascan(itf, ref)

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(wl, itf, label='interference')
    ax0_1, = ax0.plot(wl, ref, label='reference')
    ax0.legend(borderaxespad=0.2)
    ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0, = ax1.plot(sp.depth*1e6, ascan, label='Numpy fft')
    ax1.legend(borderaxespad=0.2)
    plt.show()
