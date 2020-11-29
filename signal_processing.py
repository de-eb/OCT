import numpy as np
import pandas as pd
from scipy import special, interpolate
import matplotlib.pyplot as plt

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

if __name__ == "__main__":

    # Data loading
    ref = pd.read_csv('data/201128_ref.csv', header=2, index_col=0)
    data0 = pd.read_csv('data/201128_0.csv', header=2, index_col=0)
    wl = ref.values[:,0]*1e-9  # wavelength
    bg = ref.values[:,1]  # background spectra
    sp = data0.values[:,1]  # sample spectra

    # Re-sampling
    n = len(wl)
    i = np.arange(n)
    s = (n-1)/(wl.max()-wl.min()) * (1/(1/wl.max()+i/(n-1)*(1/wl.min()-1/wl.max())) - wl.min())
    wl_fix = wl.min() + s*(wl.max()-wl.min())/(n-1)
    func_bg = interpolate.interp1d(wl, bg, kind='cubic')  # interpolation
    bg_fix = func_bg(wl_fix)
    func_sp = interpolate.interp1d(wl, sp, kind='cubic')
    sp_fix = func_sp(wl_fix)

    # Normalize
    sub = sp_fix - bg_fix

    # Windowing
    x = np.linspace(0, len(wl_fix), len(wl_fix))
    # window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    wnd = sub*window

    # x-axis calculation
    centre = int(len(wl_fix)/2)
    # depth = c*(1/(c/(wl_fix*n)))/(2*n)  # depth
    depth = wl_fix/2
    # depth = depth[centre:] - depth[centre]

    # FFT
    fft = np.abs(np.fft.ifft(wnd, axis=0))
    # fft1 = np.abs(np.fft.ifft(wnd1, axis=0))[centre:,:]

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax0 = fig.add_subplot(311, title='Resampling', xlabel='Wavelength', ylabel='Intensity [-]')
    ax0.plot(wl_fix, bg_fix, label='bg', color=(1,0,0,0.5))
    ax0.plot(wl_fix, sp_fix, label='interferogram', color=(0,1,0,0.5))
    # ax0.grid(which='both', axis='x', color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
    ax0.legend()
    ax1 = fig.add_subplot(312, title='Windowing', xlabel='Wavelength', ylabel='Intensity [-]')
    ax1.plot(wl_fix, sub, label='subtruction', color=(1,0,0,0.5))
    ax1.plot(wl_fix, wnd, label='windowed', color=(0,1,0,0.5))
    # ax0.grid(which='both', axis='x', color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.legend()
    ax2 = fig.add_subplot(313, title='A-scan', xlabel='depth[m]', ylabel='Intensity [-]')
    ax2.plot(wl_fix, fft, label='IFFT', color=(1,0,0,0.5))
    # ax0.grid(which='both', axis='x', color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
    ax2.legend()
    plt.show()
