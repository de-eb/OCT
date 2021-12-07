import os
import glob
import datetime
from re import X
import pandas as pd
import numpy as np
from scipy import special, interpolate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datapane as dp

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
        if spectra.ndim <= 1:
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
        if interference.ndim <= 1:
            ascan = ascan.reshape([ascan.size,])
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
    
    def load_spectra(self, file_path, wavelength_range=[0,2000]):
        """ Load the spectra. The data format is the same as the one saved by `self.save_spectra`.

        Parameters
        ----------
        file_path : `str`, required
            Where to load the file.
        wavelengrh_range : `list`
            Wavelength range [nm] of the spectra to be loaded.
            Specify the lower limit in the first element and the upper limit in the next element.
        
        Returns
        -------
        data : `dict`
            Data name-value pairs.
        """
        data = {}
        df = pd.read_csv(file_path, header=2, index_col=0)
        df = df[(df['Wavelength [nm]']>wavelength_range[0]) & (df['Wavelength [nm]']<wavelength_range[1])]
        if 'Wavelength [nm]' in df.columns:
            data['wavelength'] = df.loc[:, 'Wavelength [nm]'].values
        if 'Reference [-]' in df.columns:
            data['reference'] = df.loc[:, 'Reference [-]'].values
        if 'Spectra [-]' in df.columns:
            data['spectra'] = df.loc[:, 'Spectra [-]'].values
        elif 'Spectra0 [-]' in df.columns:
            data['spectra'] = df.iloc[:, df.columns.get_loc('Spectra0 [-]'):].values
        return data
    
    def load_dataset(self, sheet_name, wavelength=None):
        """ Load optical constants from the dataset.
        See `modules/tools/optical_constants_dataset.xlsx` for details.

        Parameters
        ----------
        sheet_name : `str`, required
            Name of the dataset (sheet name in xlsx file) you want to load.
        wavelength : `1d-ndarray`
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
                if wavelength is not None:
                    func = interpolate.interp1d(wl, val, kind='cubic')
                    val = func(wavelength)
                    wl = wavelength
                dataset[col] = val
                dataset['wl_'+col] = wl
        return dataset
    
    def draw_graph(self, format, upload_name=None, **kwargs):
        """ Draw a graph.

        Parameters
        ----------
        format : `str`, required
            Graph format. Specify the following.
                'spectra' : Line chart with wavelength[nm] vs intensity[-].
                'ascan' : Line chart with depth[μm] vs intensity[-].
                'bscan' : Heatmap with depth[μm] vs scanning distance[μm]  vs intensity[-].
        upload_name : `str`
            Upload the graph with this name to https://datapane.com.
            If not specified, the graph will be displayed offline.
        x : `any`
            Data to be used as the x-axis of the graph.
            If 'spectra' or 'ascan', specify a `list` of `1d-ndarray` to display multiple charts.
            If 'bscan', specify a `1d-ndarray`.
        y : `any`
            Data to be used as the y-axis of the graph.
            If 'spectra' or 'ascan', specify a `list` of `1d-ndarray` to display multiple charts.
            If 'bscan', specify a `1d-ndarray`.
        z : `any`
            Data to be used as the z-axis of the graph. If 'spectra' or 'ascan', it will not be used.
            If 'bscan', specify a `2d-ndarray` corresponding to the x-axis and y-axis, respectively.
        label : `any`
            A label for each data. If 'spectra' or 'ascan', specify a `list` of `str` to display the legend.
            If 'bscan', it will not be used.
        """
        # Plot
        if format == 'spectra' or format == 'ascan':
            fig = make_subplots(rows=1, cols=1)
            for i in range(len(kwargs['label'])):
                fig.add_trace(
                    trace=go.Scatter(
                        x=kwargs['x'][i], y=kwargs['y'][i], name=kwargs['label'][i], mode='lines'),
                    row=1, col=1)
            if format == 'spectra': xaxis = 'Wavelength [nm]'
            if format == 'ascan': xaxis = 'Depth [μm]'
            yaxis, ticksdir = 'Intensity [-]', 'inside'
        elif format == 'bscan':
            fig = go.Figure(
                data=go.Heatmap(
                    z=kwargs['z'], x=kwargs['x'], y=kwargs['y'],
                    zsmooth='fast', zmin=0, zmax=kwargs['zmax'],
                    colorbar=dict(
                        title=dict(text='Intensity [-]', side='right'),
                        exponentformat='SI', showexponent='last'),
                    colorscale='gray',))
            xaxis, yaxis, ticksdir = 'Depth [μm]', 'Scanning length [μm]', 'outside'
        # Styling
        fig.update_xaxes(
            title_text=xaxis, title_font=dict(size=14,), color='#554D51', mirror=True,
            ticks=ticksdir, exponentformat='SI', showexponent='last')
        fig.update_yaxes(
            title_text=yaxis, title_font=dict(size=14,), color='#554D51', mirror=True,
            ticks=ticksdir, exponentformat='SI', showexponent='last')
        fig.update_layout(
            template='simple_white', autosize=True, margin=dict(t=20, b=60, l=20, r=0),
            font=dict(family='Arial', size=14, color='#554D51'),
            legend=dict(
                bgcolor='rgba(0,0,0,0)', orientation='v',
                xanchor='right', yanchor='top', x=1, y=1))
        # Output
        if upload_name is not None:  # Upload to https://datapane.com (only when online)
            dp.Report(dp.Plot(fig),).upload(name=upload_name, open=True)
        else:  # View offline
            fig.show()


if __name__ == "__main__":

    # Data loading
    dh = DataHandler()
    data = dh.load_spectra('data/data.csv', wavelength_range=[770,910])
    # dataset = dh.load_dataset('PET', data['wavelength'])

    # Signal processing
    sp = SignalProcessor(data['wavelength'], 1.0)
    ascan = sp.generate_ascan(data['spectra'], data['reference'])

    # Show Graph
    dh.draw_graph(format='A-scan', y=[ascan,], x=[sp.depth*1e6], label=['Numpy IFFT',])
    # dh.draw_graph(mode='B-scan', x=sp.depth*1e6, y=np.arange(300), z=ascan.T, zmax=0.004)
