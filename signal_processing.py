import numpy as np
from scipy import signal, interpolate
import matplotlib.pyplot as plt

if __name__ == "__main__":

    # Data loading
    data = np.loadtxt('data/200902_0.csv', delimiter=',')
    wl = data[:,0] * 1e-9 # wavelength
    itf = data[:,1]  # interference spectra
    ref = np.loadtxt('data/200902_0_ref.csv', delimiter=',')[:,1]  # reference spectra

    # Background Subtraction
    tmp = itf - ref

    # Re-Sampling
    n = len(wl)
    i = np.arange(n)
    s = ((n-1)/(np.amax(wl)-np.amin(wl)) * (1/(1/np.amax(wl)+i/(n-1)*(1/np.amin(wl)-1/np.amax(wl))) - np.amin(wl)))
    wl_fix = np.amin(wl) + s*(np.amax(wl)-np.amin(wl))/(n-1)
    # tmp = signal.resample(tmp, n, wl)  # up sampling
    func = interpolate.interp1d(wl, tmp, kind='cubic')  # interpolation
    tmp = func(wl_fix)
    # tmp = np.pad(tmp, [1, n-1])
    # tmp = np.concatenate([tmp, tmp[::-1]])

    # Axis conversion
    k = 2*np.pi/wl_fix  # wabe number
    freq = 3e8/wl_fix  # frequency
    time = 1/freq  # cycle
    depth = 3e8*time/(2)  # depth
    depth = depth - np.amin(depth)

    # FFT
    tmp = np.abs(np.fft.ifft(tmp))

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Measurement results")
    ax.set_xlabel("depth [m]")
    ax.set_ylabel("magnitude [-]")
    # ax.scatter(wl, itf, s=10, label='interference')
    # ax.scatter(wl, ref, s=10, label='reference')
    # ax.scatter(wl, sub, s=10, label='Background Subtraction')
    # ax.scatter(wl, sub_fix, s=10, label='Re-Sampling')
    ax.plot(tmp, label='FFT')
    ax.legend()
    plt.show()