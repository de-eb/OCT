import numpy as np
from scipy.special import iv
import matplotlib.pyplot as plt


# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.46  # Refractive index of the sample. cellulose = 1.46
alpha = 1.  # oversampling factor

if __name__ == "__main__":

    # Data loading
    ref = np.loadtxt('data/.csv', delimiter=',')
    freq = ref[:,0] * 1e9 # frequency
    bg = ref[:,1]  # background spectra
    raw = np.loadtxt('data/.csv', delimiter=',')[:,1]  # sample spectra

    # Background subtruction
    tmp = raw - bg

    # Re-sampling
    f_med = np.median(freq)
    wl = int(0.5*len(raw))  # window length
    delta_f = (np.amax(freq)-np.amin(freq))/(len(raw))
    beta = np.pi()*np.sqrt(wl**2*(alpha-1/2)**2/alpha**2 - 0.8)  # design parameter
    arg = beta
    window = iv(v=0, z=arg)

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