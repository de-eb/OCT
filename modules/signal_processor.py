import os
import glob
import datetime
import pandas as pd
import numpy as np
from scipy import special, interpolate


class SignalProcessor():
    """ Class that summarizes the various types of signal processing for OCT.
    """
    c = 2.99792458e8  # Speed of light in a vacuum [m/sec].

    def __init__(self, wavelength, n, alpha=1.5) -> None:
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
        self.__wl_fix = self.__wl.min() + s*(self.__wl.max()-self.__wl.min())/(self.__ns-1)  # Fixed Wavelength
        
        # Generating window functions
        x = np.linspace(0, self.__ns, self.__ns)
        self.__window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
        self.__window = np.reshape(self.__window, [self.__window.shape[0],1])

        # Axis conversion for FFT
        freq = SignalProcessor.c / (self.__wl_fix*1e-9*n)
        fs = 2*freq.max()  # Nyquist frequency
        self.__nf = self.__ns * 2 # Number of samples after IFFT
        t = self.__nf / fs  # Maximum value of time axis after IFFT
        self.__depth = np.linspace(0, SignalProcessor.c*t/2, self.__ns)

    @property
    def depth(self) -> np.ndarray:
        """ Horizontal axis after FFT (depth [m])
        """
        return self.__depth

    def resample(self, spectra, kind='cubic') -> np.ndarray:
        """ Resamples the spectra.

        Parameters
        ----------
        spectra : `ndarray`, required
            Spectra sampled evenly in the wavelength space.
            For data in 2 or more dimensions, use axis0 as the wavelength axis.
        kind : `str`
            Data interpolation methods. For more information, see
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html

        Returns
        -------
        `ndarray`
            Spectra resampled evenly in the frequency space.
        """
        resampled = np.zeros_like(spectra)
        if spectra.ndim == 1:
            func = interpolate.interp1d(self.__wl, spectra, kind)
            resampled = np.reshape(func(self.__wl_fix), [spectra.shape[0],1])
        elif spectra.ndim == 2:
            for i in range(spectra.shape[1]):
                func = interpolate.interp1d(self.__wl, spectra[:,i], kind)
                resampled[:,i] = func(self.__wl_fix)
        elif spectra.ndim == 3:
            for j in range(spectra.shape[2]):
                for i in range(spectra.shape[1]):
                    func = interpolate.interp1d(self.__wl, spectra[:,i,j], kind)
                    resampled[:,i,j] = func(self.__wl_fix)
        return self.normalize(resampled, axis=0)

    def remove_background(self, spectra) -> np.ndarray:
        """ Removes the reference spectra from the interference spectra.

        Parameters
        ----------
        spectra : `ndarray`, required
            Spectra. Normally, specify the interference spectra after resampling.
            For data in 2 or more dimensions, use axis0 as the wavelength axis.

        Returns
        -------
        `ndarray`
            Spectra after reference spectra removal.
        """
        return spectra - self.__ref_fix
    
    def apply_window(self, spectra) -> np.ndarray:
        """ Multiply the spectra by the window function.

        Parameters
        ----------
        spectra : `ndarray`, required
            Spectra after removing the background.

        Returns
        -------
        `ndarray`
            Spectra after applying the window function.
        """
        return spectra*self.__window
    
    def apply_ifft(self, spectra) -> np.ndarray:
        """ Apply IFFT to the spectra and convert it to time domain data (i.e. A-scan).

        Parameters
        ----------
        spectra : `ndarray`, required
            Spectra after applying the window function.

        Returns
        -------
        `ndarray`
            Data after IFFT.
        """
        magnitude = np.abs(np.fft.ifft(spectra, n=self.__nf, axis=0))
        return magnitude[:self.__ns]
    
    def set_reference(self, spectra) -> np.ndarray:
        """ Specify the reference spectra. This spectra will be used in later calculations.

        Parameters
        ----------
        spectra : `1d-ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.
        
        Returns
        -------
        `1d-ndarray`
            Reference spectra after resampling.
        """
        self.__ref_fix = self.resample(spectra)
        return self.__ref_fix
    
    def normalize(self, x, axis=None) -> np.ndarray:
        """ Min-Max Normalization.

        Parameters
        ----------
        x : `ndarray`, required
            Array to be normalized.
        
        axis : `int`
            If specified, normalization is performed according to the maximum and minimum values along this axis.
            Otherwise, normalization is performed by the maximum and minimum values of the entire array.
        
        Returns
        -------
        `1d-ndarray`
            An array normalized between a minimum value of 0 and a maximum value of 1.
        """
        min = x.min(axis=axis, keepdims=True)
        max = x.max(axis=axis, keepdims=True)
        return (x-min)/(max-min)
    
    def generate_ascan(self, interference, reference) -> np.ndarray:
        """ Performs a series of signal processing in one step.

        Parameters
        ----------
        interference : `ndarray`, required
            Spectra of interference light only, sampled evenly in wavelength space.
        reference : `ndarray`, required
            Spectra of reference light only, sampled evenly in wavelength space.

        Returns
        -------
        ascan : `ndarray`
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


class DataHandler():
    """ Class for reading, writing, and visualizing data.
    """

    def __init__(self):
        """
        """
        pass

    def save_spectra(self, wavelength, reference=None, spectra=None, file_path=None, memo=''):
        """ Save the spectral data in a uniform format.

        Parameters
        ----------
        wavelength : `1d-ndarray`, required
            Wavelength [nm] data corresponding to spectra.
        reference : `1d-ndarray`
            Spectra of reference light only. If it is not specified, it will not be recorded.
        spectra : `ndarray`
            Spectra, such as interference light.
            When specifying 2-dimensional data, axis0 should correspond to the wavelength data.
        file_path : `str`
            Where file is stored.
            If not specified, the file will be automatically numbered and saved in `data/`.
        memo : `str`
            Additional information to be included in the header of the file.
        """
        # Data formatting
        columns = ['Wavelength [nm]']
        data = wavelength.reshape([wavelength.size,1])
        if reference is not None:
            columns.append('Reference [-]')
            data = np.hstack((data,reference.reshape([wavelength.size,1])))
        if spectra is not None:
            if spectra.ndim == 1:
                columns.append('Spectra [-]')
                spectra = spectra.reshape([wavelength.size,1])
            elif spectra.ndim == 2:
                columns += ['Spectra{} [-]'.format(i) for i in range(spectra.shape[1])]
            data = np.hstack((data,spectra))
        df = pd.DataFrame(data=data, columns=columns, dtype='float')
        # File numbering
        timestamp = datetime.datetime.now()
        if file_path is None:
            files = [os.path.basename(p) for p in glob.glob('data/*') if os.path.isfile(p)]
            tag = timestamp.strftime('%y%m%d')
            i = 0
            while tag + '_{}.csv'.format(i) in files: i+=1
            file_path = 'data/' + tag + '_{}.csv'.format(i)
        # Save
        with open(file_path, mode='w') as f:
            f.write('date,{}\nmemo,{}\n'.format(timestamp.strftime('%Y-%m-%d %H:%M:%S'), memo))
        df.to_csv(file_path, mode='a')
        print("Saved the spectra to {} .".format(file_path))
    
    def load_spectra(self, file_path):
        """ Load the spectra. The data format is the same as the one saved by `self.save_spectra`.

        file_path : `str`, required
            Where to load the file.
        
        Returns
        -------
        dataset : `dict`
            Data name-value pairs.
        """
        data = {}
        df = pd.read_csv(file_path, header=2, index_col=0)
        if 'Wavelength [nm]' in df.columns:
            data['wavelength'] = df.loc[:, 'Wavelength [nm]'].values
        if 'Reference [-]' in df.columns:
            data['reference'] = df.loc[:, 'Reference [-]'].values
        if 'Spectra [-]' in df.columns:
            data['spectra'] = df.loc[:, 'Spectra [-]'].values
        elif 'Spectra0 [-]' in df.columns:
            data['spectra'] = df.iloc[:, df.columns.get_loc('Spectra0 [-]'):].values
        return data
    
    def load_dataset(self, sheet_name, new_wl=None):
        """ Load optical constants from the dataset.
        See `modules/tools/optical_constants_dataset.xlsx` for details.

        Parameters
        ----------
        sheet_name : `str`, required
            Name of the dataset (sheet name in xlsx file) you want to load.
        new_wl : `1d-ndarray`
            Wavelength axis data for resampling.
            If not specified, the original raw data will be returned.

        Returns
        -------
        dataset : `dict`
            Available data and the corresponding wavelengths.
            Note that even if the data name is the same, the units may be different,
            so be careful when evaluating the data.
        """
        dataset = {}
        df = pd.read_excel('modules/tools/optical_constants_dataset.xlsx', sheet_name, header=3, index_col=0)
        for col in list(df.columns):
            if 'wl' not in col:
                val = df.loc[:, col].dropna().values
                wl = df.iloc[:, df.columns.get_loc(col)-1].dropna().values
                if new_wl is not None:
                    func = interpolate.interp1d(wl, val, kind='cubic')
                    val = func(new_wl)
                    wl = new_wl
                dataset[col] = val
                dataset['wl_'+col] = wl
        return dataset


if __name__ == "__main__":

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import datapane as dp

    st = 762  # Calculation range (Start)
    ed = 953  # Calculation range (End)

    # Data loading
    data = pd.read_csv('data/data.csv', header=2, index_col=0)
    wl = data.values[st:ed,0]  # wavelength
    ref = data.values[st:ed,1]  # background spectra
    itf = data.values[st:ed,2:]  # sample spectra

    # Signal processing
    sp = SignalProcessor(wl, 1.0)
    ascan = sp.generate_ascan(itf, ref)

    # plot
    palette = {'black':'#554D51', 'gray':'#90868B', 'red':'#E07772', 'green':'#B5DF6A', 'blue':'#48CAD6'}
    fig = make_subplots(subplot_titles=('B-scan',), rows=1, cols=1, vertical_spacing=0.2)
    fig.add_trace(row=1, col=1, trace=go.Heatmap(z=ascan.T, x=sp.depth*1e6, y=np.arange(300), colorbar=dict(len=0.8, title=dict(text='Intensity [-]', side='right')), zmin=0, zmax=0.003))
    
    # styling
    fig.update_xaxes(row=1, col=1, title_text='Depth [μm]',color=palette['black'], mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.update_yaxes(row=1, col=1, title_text='Scanning length [μm]',color=palette['black'], mirror=True, ticks='inside', showexponent='last', exponentformat='SI')
    fig.update_layout(
        template='simple_white', autosize=True,
        margin=dict(t=20, b=60, l=10, r=10),
        font=dict(family='Arial', size=14, color=palette['black']),
        legend=dict(bgcolor='rgba(0,0,0,0)', orientation='v', xanchor='right', yanchor='top', x=1, y=1, tracegroupgap=170)
    )
    fig.for_each_xaxis(lambda axis: axis.title.update(font=dict(size=14,)))
    fig.for_each_yaxis(lambda axis: axis.title.update(font=dict(size=14,)))
    fig.update_annotations(font=dict(size=14,))
    
    # Upload to https://datapane.com (only when online)
    dp.Report(dp.Plot(fig),).upload(name="B-scan test", open=True)
    # fig.show()  # View offline
