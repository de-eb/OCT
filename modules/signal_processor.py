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

    import chart_studio
    import chart_studio.plotly as py
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st = 762  # Calculation range (Start)
    ed = 953  # Calculation range (End)

    # Data loading
    data = pd.read_csv('data/data.csv', header=2, index_col=0)
    wl = data.values[st:ed,0]  # wavelength
    ref = data.values[st:ed,1]  # background spectra
    itf = data.values[st:ed,2]  # sample spectra
    
    cellulose = DatasetHandler('Cellulose', wl)
    itf_cellulose = itf*cellulose.alpha

    # Signal processing
    sp = SignalProcessor(wl, 1.0)

    ascan = sp.generate_ascan(itf, ref)
    ascan_cellulose = sp.generate_ascan(itf_cellulose, ref)

    # plot
    fig = make_subplots(subplot_titles=('Spectra','A-scan'), rows=2, cols=1, vertical_spacing=0.2)
    fig.add_trace(go.Scatter(x=wl, y=ref, name='reference', mode='lines', legendgroup='1'), row=1, col=1)
    fig.add_trace(go.Scatter(x=wl, y=itf, name='interference', mode='lines', legendgroup='1'), row=1, col=1)
    fig.add_trace(go.Scatter(x=wl, y=itf_cellulose, name='weighted by cellulose', mode='lines', legendgroup='1'), row=1, col=1)
    fig.add_trace(go.Scatter(x=sp.depth*1e6, y=ascan, name='raw', mode='lines', legendgroup='2'), row=2, col=1)
    fig.add_trace(go.Scatter(x=sp.depth*1e6, y=ascan_cellulose, name='weighted by cellulose', mode='lines', legendgroup='2'), row=2, col=1)
    # styling
    fig.update_xaxes(row=1, col=1, title_text='Wavelength [nm]', linewidth=1, linecolor='#554D51', mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.update_yaxes(row=1, col=1, title_text='Intensity [-]', linewidth=1, linecolor='#554D51', mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.update_xaxes(row=2, col=1, title_text='Depth [μm]', linewidth=1, linecolor='#554D51', mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.update_yaxes(row=2, col=1, title_text='Intensity [-]', linewidth=1, linecolor='#554D51', mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.for_each_xaxis(lambda axis: axis.title.update(font=dict(family='Arial', size=18, color='#554D51')))
    fig.for_each_yaxis(lambda axis: axis.title.update(font=dict(family='Arial', size=18, color='#554D51')))
    fig.update_annotations(font=dict(family='Arial', size=18, color='#554D51'))
    fig.update_layout(
        template='simple_white', width=1000, height=800,
        font=dict(family='Arial', size=18, color='#554D51'),
        title=dict(text='', font=dict(family='Arial', size=18, color='#554D51'),),
        legend=dict(orientation='v', xanchor='right', yanchor='top', x=1, y=1, tracegroupgap = 270, font=dict(family='Arial', size=18, color='#554D51'), bgcolor='rgba(0,0,0,0)')
    )
    
    # Upload to https://chart-studio.plotly.com (only when online)
    chart_studio.tools.set_credentials_file(username='YOUR_ACCOUNT_NAME', api_key='YOUR_API_KEY')
    py.plot(fig, filename='graph', auto_open=True)
    # fig.show()  # View offline
