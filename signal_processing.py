import numpy as np
import pandas as pd
from scipy import special
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
    ref = pd.read_csv('data/201015_ref.csv', header=2, index_col=0)
    data0 = pd.read_csv('data/201016_1.csv', header=2, index_col=0)
    data1 = pd.read_csv('data/201023_0.csv', header=2, index_col=0)
    freq = ref.values[:,0]*1e9 # frequency
    bg = ref.values[:,1].reshape((len(freq),1))  # background spectra
    raw0 = data0.values[:,1:].reshape((len(freq),-1))  # sample spectra
    raw1 = data1.values[:,1:].reshape((len(freq),-1))

    # Normalize
    sub0 = raw0/bg
    sub1 = raw1/bg

    # Re-sampling
    x = np.linspace(0, len(freq), len(freq))
    # window = 0.42 - 0.5*np.cos(2*np.pi*x) + 0.08*np.cos(4*np.pi*x)  # Blackman window
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    window = window.reshape((len(freq),1))
    wnd0 = sub0*window
    wnd1 = sub1*window
    wnd2 = bg*window

    # x-axis calculation
    centre = int(len(freq)/2)
    time = np.arange(len(freq))/(len(freq)*(freq[1]-freq[0]))
    depth = time*c/(2*n) * 1e3
    depth = depth[centre:] - depth[centre]

    # fs = 2*np.amax(freq)  # sampling freq
    # d = len(freq)/fs  # time window length
    # depth = np.linspace(0, d*c/(2*n), len(freq))*1e3  # [mm]
    # depth = depth[centre:] - depth[centre]

    # FFT
    fft0 = np.abs(np.fft.ifft(wnd0, axis=0))[centre:,:]
    fft1 = np.abs(np.fft.ifft(wnd1, axis=0))[centre:,:]
    fft2 = np.abs(np.fft.ifft(wnd2, axis=0))[centre:,:]

    # Show Graph
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax0 = fig.add_subplot(211, title='A-scan change with sample displacement (coverslip, in the optical axis)', xlabel='Depth [mm]', ylabel='Intensity [-]')
    ax0.plot(depth, fft0[:,0]+0.09, label='0μm', color=(1,0,0,0.5))
    ax0.plot(depth, fft0[:,1]+0.06, label='1μm', color=(0,0,1,0.5))
    ax0.plot(depth, fft0[:,2]+0.03, label='2μm', color=(0,1,0,0.5))
    ax0.plot(depth, fft2, label='BG', color=(0,0,0,0.5))
    ax0.grid(which='both', axis='x', color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
    ax0.legend()
    
    ax3 = fig.add_subplot(212, title='A-scan change with sample displacement (cellophan tape, in the optical axis)', xlabel='Depth [mm]', ylabel='Intensity [-]')
    ax3.plot(depth, fft1[:,0]+0.09, label='0μm', color=(1,0,0,0.5))
    ax3.plot(depth, fft1[:,1]+0.06, label='1μm', color=(0,0,1,0.5))
    ax3.plot(depth, fft1[:,2]+0.03, label='2μm', color=(0,1,0,0.5))
    ax3.plot(depth, fft2, label='BG', color=(0,0,0,0.5))
    ax3.grid(which='both', axis='x', color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
    ax3.legend()
    plt.show()