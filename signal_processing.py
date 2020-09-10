import numpy as np
from scipy import signal, interpolate
import matplotlib.pyplot as plt


# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.46  # Refractive index of the sample. cellulose = 1.46
d = 0.05e-3

if __name__ == "__main__":

    # Data loading
    data = np.loadtxt('data/200902_0.csv', delimiter=',')
    wl = data[:,0] * 1e-9 # wavelength
    itf = data[:,1]  # interference spectra
    ref = np.loadtxt('data/200902_0_ref.csv', delimiter=',')[:,1]  # reference spectra

    # Background Subtraction
    tmp = itf - ref

    # Re-Sampling
    N = len(wl)
    i = np.arange(N)
    s = (N-1)/(np.amax(wl)-np.amin(wl)) * (1/(1/np.amax(wl)+i/(N-1)*(1/np.amin(wl)-1/np.amax(wl))) - np.amin(wl))
    wl_fix = np.amin(wl) + s*(np.amax(wl)-np.amin(wl))/(N-1)
    func = interpolate.interp1d(wl, tmp, kind='cubic')  # interpolation
    tmp = func(wl_fix)

    # Axis conversion
    depth = c*(1/(c/(wl_fix*n)))/(2*n)  # depth
    depth = depth - depth[int(N/2)]

    # FFT
    tmp = np.abs(np.fft.ifft(tmp))

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("A-scan")
    ax.set_xlabel("depth [nm]")
    ax.set_ylabel("magnitude [-]")
    ax.plot(depth*1e9, tmp, label='FFT')
    # ax.legend()
    plt.show()