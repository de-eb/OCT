import numpy as np
import pandas as pd
from scipy import special, interpolate
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

# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.4  # Refractive index of the sample. cellulose = 1.46
alpha = 1.5  # design factor of Kaiser window

st = 762
ed = 953


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
    depth_axis = np.linspace(0, xmax, int(1e2))
    time = 2*(n*depth_axis*1e-3)/c
    for i in range(len(freq)):
        if i==0:
            result = itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
        else:
            result += itf[i]*np.sin(2*np.pi*time*freq[i]*1e12)
    result /= len(freq)
    return depth_axis, abs(result)


if __name__ == "__main__":

    # Data loading
    ref = pd.read_csv('data/210729_ref.csv', header=2, index_col=0)
    data = pd.read_csv('data/210729.csv', header=2, index_col=0)
    wl = ref.values[st:ed,0]  # wavelength
    bg = ref.values[st:ed,1]  # background spectra
    sp = data.values[st:ed,1:]  # sample spectra

    # x-axis conversion
    n = len(wl)
    i = np.arange(n)
    s = (n-1)/(wl.max()-wl.min()) * (1/(1/wl.max()+i/(n-1)*(1/wl.min()-1/wl.max())) - wl.min())
    wl_fix = wl.min() + s*(wl.max()-wl.min())/(n-1)
    centre = int(n/2)
    # depth = wl_fix/2  # depth = c*(1/(c/(wl_fix*n)))/(2*n)

    # Re-sampling
    func_bg = interpolate.interp1d(wl, bg, kind='cubic')  # interpolation
    bg_fix = func_bg(wl_fix)

    sp_fix = np.zeros_like(sp)
    for i in range(sp_fix.shape[1]):
        func_sp = interpolate.interp1d(wl, sp[:,i], kind='cubic')
        sp_fix[:,i] = func_sp(wl_fix)

    # Normalize
    sub = sp_fix/np.amax(sp_fix, axis=0, keepdims=True) - (bg_fix/bg_fix.max()).reshape((n,1))
    # sub = sp_fix - bg_fix.reshape((n,1))

    # Windowing
    x = np.linspace(0, n, n)
    # window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    wnd = sub*window.reshape((n,1))

    # FFT
    fft = np.abs(np.fft.ifft(wnd, axis=0))[centre:]
    depth_, fft_ = inverse_ft(c/wl_fix*1e-3, wnd[:,0], 1., n)

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax0 = fig.add_subplot(211, title='Numpy FFT', xlabel='data num.[-]', ylabel='Intensity [-]')
    ax0.plot(fft[:,0], color=(0,0,1,0.5))
    ax0.legend()
    ax1 = fig.add_subplot(212, title='New FFT', xlabel='depth [mm]', ylabel='Intensity [-]')
    ax1.plot(depth_, fft_, color=(0,0,1,0.5))
    ax1.legend()
    plt.show()
