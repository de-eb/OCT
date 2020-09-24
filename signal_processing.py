import numpy as np
from scipy import signal, interpolate
import matplotlib.pyplot as plt


# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.46  # Refractive index of the sample. cellulose = 1.46
d = 0.05e-3

if __name__ == "__main__":

    # Data loading
    data = np.loadtxt('data/200908_0.csv', delimiter=',')
    freq = data[:,0] * 1e9 # frequency
    itf = data[:,1]  # interference spectra
    ref = np.loadtxt('data/200908_0_ref.csv', delimiter=',')[:,1]  # reference spectra

    # Background correction
    tmp = itf/(2*ref)
    # tmp = itf - ref

    # x-axis calculation
    centre = int(len(freq)/2)
    time = 1. / (np.amax(freq)-np.amin(freq)) * np.arange(0,len(freq))
    depth = time*c / (2*n)
    depth = depth - np.amin(depth)
    depth = depth - depth[centre]

    # FFT
    tmp = np.abs(np.fft.ifft(tmp))

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("A-scan")
    ax.set_xlabel("depth [mm]")
    ax.set_ylabel("magnitude [-]")
    ax.plot(depth[centre:]*1e3, tmp[centre:])
    # ax.set_title("spectral interferogram")
    # ax.set_xlabel("frequency [THz]")
    # ax.set_ylabel("voltage [V]")
    # ax.plot(freq*1e-12, itf)
    plt.show()