""" Module for reading, writing, and visualizing data.

"""
import os
import glob
import datetime
import pandas as pd
import numpy as np
from scipy import interpolate
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def save_spectra(wavelength, reference=None, spectra=None, file_path=None, memo=''):
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
    # Save
    file_path = generate_filename('csv')
    with open(file_path, mode='w') as f:
        f.write('date,{}\nmemo,{}\n'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), memo))
    df.to_csv(file_path, mode='a')
    print("Saved the spectra to {} .".format(file_path))


def load_spectra(file_path, wavelength_range=[0,2000]):
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


def load_dataset(sheet_name, wavelength=None):
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


def draw_graph(format, **kwargs):
    """ Draw a graph.

    Parameters
    ----------
    format : `str`, required
        Graph format. Specify the following.
            'spectra' : Line chart with wavelength[nm] vs intensity[-].
            'ascan' : Line chart with depth[μm] vs intensity[-].
            'bscan' : Heatmap with depth[μm] vs scanning distance[μm]  vs intensity[-].
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
    name : `any`
        Data name. If 'spectra' or 'ascan', specify a `list` of `str` to display the legend.
        If 'bscan', it will not be used.
    xlabel : `str`
        If specified, x-axis name will be changed from the default.
    ylabel : `str`
        If specified, y-axis name will be changed from the default.
    """
    # Plot
    if format == 'spectra' or format == 'ascan':
        fig = make_subplots(rows=1, cols=1)
        for i in range(len(kwargs['name'])):
            fig.add_trace(
                trace=go.Scatter(
                    x=kwargs['x'][i], y=kwargs['y'][i], name=kwargs['name'][i], mode='lines'),
                row=1, col=1)
        xlabel, ylabel, ticksdir = 'Wavelength [nm]', 'Intensity [-]', 'inside'
        if format == 'ascan': xlabel = 'Depth [μm]'
    elif format == 'bscan':
        fig = go.Figure(
            data=go.Heatmap(
                z=kwargs['z'], x=kwargs['x'], y=kwargs['y'],
                zsmooth='fast', zmin=0, zmax=kwargs['zmax'],
                colorbar=dict(
                    title=dict(text='Intensity [-]', side='right'),
                    exponentformat='SI', showexponent='last'),
                colorscale='gray',))
        xlabel, ylabel, ticksdir = 'Depth [μm]', 'Scanning length [μm]', 'outside'
    if 'xlabel' in kwargs: xlabel = kwargs['xlabel']
    if 'ylabel' in kwargs: ylabel = kwargs['ylabel']
    # Styling
    fig.update_xaxes(
        title_text=xlabel, title_font=dict(size=14,), color='#554D51', mirror=True,
        ticks=ticksdir, exponentformat='SI', showexponent='last')
    fig.update_yaxes(
        title_text=ylabel, title_font=dict(size=14,), color='#554D51', mirror=True,
        ticks=ticksdir, exponentformat='SI', showexponent='last')
    fig.update_layout(
        template='simple_white', autosize=True, margin=dict(t=30, b=30, l=30, r=30),
        font=dict(family='Arial', size=14, color='#554D51'),
        legend=dict(bgcolor='rgba(0,0,0,0)', xanchor='right', yanchor='top', x=1, y=1))
    # Output
    file_name = generate_filename('html')
    fig.write_html(file_name, include_plotlyjs='cdn', auto_open=True)


def generate_filename(extension, directory='data'):
    """ Automatically generates unique file name that include relative path and extension.
    This prevents overwriting of already existing measurement data, etc.

    Parameters
    ----------
    extension : `str`, required
        File extension to be added to file name.
    directory : `str`
        Relative path to be appended to the file name.
    
    Returns
    -------
    filename : `str`
        File name containing relative path and extension.
    """
    timestamp = datetime.datetime.now()
    files = [os.path.basename(p) for p in glob.glob('{}/*'.format(directory)) if os.path.isfile(p)]
    tag = timestamp.strftime('%y%m%d')
    i = 0
    while '{}_{}.{}'.format(tag,i,extension) in files: i+=1
    return '{}/{}_{}.{}'.format(directory,tag,i,extension)
