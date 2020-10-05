import numpy as np
from scipy import special
import matplotlib.pyplot as plt


# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1  # Refractive index of the sample. cellulose = 1.46

if __name__ == "__main__":

    # Data loading
    ref = np.loadtxt('data/201003_bg_mean.csv', delimiter=',')
    freq = ref[:,0]*1e9 # frequency
    bg = ref[:,1]  # background spectra
    raw = np.loadtxt('data/201003_3.csv', delimiter=',')[:,1]  # sample spectra

    # Background subtruction
    tmp = np.abs(raw-bg)

    # Re-sampling
    x = np.linspace(0, len(freq), len(freq))
    window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
    # alpha = 10.
    # window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    tmp = tmp*window

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
    ax.set_title("Change in A-scan")
    ax.set_xlabel("depth [mm]")
    ax.set_ylabel("magnitude [-]")
    ax.plot(depth[centre:]*1e3, tmp[centre:], label='0μm', color=(1,0,0,0.5))
    plt.legend()
    plt.show()