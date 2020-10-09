import numpy as np
from scipy import special
import matplotlib.pyplot as plt

# Graph settings
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams['font.size'] = 14
plt.rcParams['axes.linewidth'] = 1.0

# Constants
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.5  # Refractive index of the sample. cellulose = 1.46

if __name__ == "__main__":

    # Data loading
    ref = np.loadtxt('data/201009_ref2.csv', delimiter=',')
    freq = ref[:,0]*1e9 # frequency
    bg = ref[:,1]  # background spectra
    raw = np.loadtxt('data/201009_6.csv', delimiter=',')[:,1]  # sample spectra

    # Background subtruction
    sub = raw/bg

    # Re-sampling
    x = np.linspace(0, len(freq), len(freq))
    # window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
    alpha = 1.5
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    wnd = sub*window

    # x-axis calculation
    centre = int(len(freq)/2)
    time = 1. / (np.amax(freq)-np.amin(freq)) * np.arange(0,len(freq))
    # time = 1. / freq
    depth = time*c / (2*n)
    depth = depth - np.amin(depth)
    depth = depth - depth[centre]

    # FFT
    fft = np.abs(np.fft.ifft(wnd))

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax1 = fig.add_subplot(311, title='Interferogram', xlabel='Frequency [THz]', ylabel='Voltage [V]')
    ax1.plot(freq*1e-12, bg, label='Reference', color=(1,0,0,0.5))
    ax1.plot(freq*1e-12, raw, label='Sample (coverslip)', color=(0,0,1,0.5))
    ax1.legend()
    ax2 = fig.add_subplot(312, title='Re-sampling', xlabel='Frequency [THz]', ylabel='Intensity [-]')
    ax2.plot(freq*1e-12, sub, label='Normalized', color=(1,0,0,0.5))
    ax2.plot(freq*1e-12, wnd, label='Kaiser α=1.5', color=(0,0,1,0.5))
    ax2.legend()
    ax3 = fig.add_subplot(313, title='A-scan', xlabel='Depth [mm]', ylabel='Intensity [-]')
    ax3.plot(depth[centre:]*1e3, fft[centre:], color=(0,0,1,0.5))
    ax3.legend()
    plt.show()