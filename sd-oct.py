import datetime
from multiprocessing import Process, Queue
import numpy as np
import cv2
import pandas as pd
from scipy import special, interpolate
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12, PmaError
from modules.fine01r import Fine01r
from modules.ncm6212c import Ncm6212c
from modules.artcam130mi import ArtCam130

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
alpha = 1.5  # Design factor of Kaiser window
st = 762  # Calculation range (Start) of spectrum [nm]
ed = 953  # Calculation range (End) of spectrum [nm]


def profile_beam(q, window_scale, exposure_time):

    camera = ArtCam130()
    camera.open(exposure_time)

    while True:
        img = camera.capture()
        img = cv2.resize(img , (int(img.shape[1]*window_scale), int(img.shape[0]*window_scale)))
        centre_v = int(img.shape[0]/2)
        centre_h = int(img.shape[1]/2)
        cv2.line(img, (centre_h, 0), (centre_h, img.shape[0]), 255, thickness=1, lineType=cv2.LINE_4)
        cv2.line(img, (0, centre_v), (img.shape[1], centre_v), 255, thickness=1, lineType=cv2.LINE_4)
        cv2.imshow('capture', img)

        key = cv2.waitKey(10)
        q.put(key)
        if key == 27:  # ESC key to exit
            break
        elif key == ord('s'):  # 'S' key to save image
            cv2.imwrite('data/image.png', img)
            print("The image was saved.")

    camera.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    # Device settings
    pma = Pma12(dev_id=5)  # Spectrometer
    stage1 = Fine01r('COM11')  # piezo stage (mirror side)
    stage2 = Ncm6212c('COM10')  # piezo stage (sample side)
    q = Queue()
    p = Process(target=profile_beam, args=(q, 0.8, 1000))  # Beam profiler
    p.start()

    # Parameter initialization
    spec_ref = None
    spec_itf = np.zeros_like(pma.wavelength, dtype=float)
    err = False
    pos_a = 0
    pos_b = 0
    wl = pma.wavelength[st:ed]
    n = len(wl)
    i = np.arange(n)
    s = (n-1)/(wl.max()-wl.min()) * (1/(1/wl.max()+i/(n-1)*(1/wl.min()-1/wl.max())) - wl.min())
    wl_fix = wl.min() + s*(wl.max()-wl.min())/(n-1)  # Fixed Wavelength
    x = np.linspace(0, n, n)
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(wl, spec_itf[st:ed], label='interference')
    ax0_1, = ax0.plot(wl, spec_itf[st:ed], label='reference')
    ax0.legend()
    ax1 = fig.add_subplot(212, title='A-scan', xlabel='data num.[-]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0 = ax1.plot(spec_itf[st:ed], label='Numpy fft')
    
    # Device initialization
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)
    pma.set_parameter(shutter=1)

    while True:
        key = q.get()
        if key == 27:  # ESC key to exit
            break
        elif key == ord('r'):  # update reference data
            spec_ref = pma.read_spectra(averaging=100)
            func_ref = interpolate.interp1d(wl, spec_ref[st:ed], kind='cubic')
            spec_ref_fix = func_ref(wl_fix)
            print("Reference data updated.")
            ax0_1.set_data(wl, spec_ref)

        elif key == ord('s'):  # 'S' key to save data
            spec_itf = pma.read_spectra(averaging=100)  # update interference data
            with open('data/data.csv', mode='w') as f:
                f.write('date,{}\nmemo,\n'.format(datetime.datetime.now().isoformat()))
            df = pd.DataFrame(
                data=np.hstack((pma.wavelength, spec_ref, spec_itf)),
                columns=['Wavelength [nm]', 'Reference [-]', 'Interference [-]'],
                dtype='float')
            df.to_csv('data/data.csv', mode='a')
            print("The spectra were saved.")

        elif key == ord('j'):  # Stage Operation: UP
            pos_a += 100
            stage2.absolute_move(axis='A', position=pos_a)
            print("Stage position [nm]: {},{}".format(pos_a,pos_b))
        elif key == ord('h'):  # Stage Operation: DOWN
            pos_a -= 100
            stage2.absolute_move(axis='A', position=pos_a)
            print("Stage position [nm]: {},{}".format(pos_a,pos_b))
        elif key == ord('f'):  # Stage Operation: LEFT
            pos_b += 100
            stage2.absolute_move(axis='B', position=pos_b)
            print("Stage position [nm]: {},{}".format(pos_a,pos_b))
        elif key == ord('g'):  # Stage Operation: RIGHT
            pos_b -= 100
            stage2.absolute_move(axis='B', position=pos_b)
            print("Stage position [nm]: {},{}".format(pos_a,pos_b))

        else:  # Spectral measurement
            try:
                spec_itf = pma.read_spectra(averaging=1)
            except PmaError as e:
                err = True
                print(e, end="\r")
            else:
                if err:
                    print("                            ")
                    err= False
        
        if spec_ref is not None:  # Signal processing
            # Interpolation
            func_itf = interpolate.interp1d(wl, spec_itf[st:ed], kind='cubic')
            spec_itf_fix = func_itf(wl_fix)
            # Normalize
            sub = spec_itf_fix/spec_itf_fix.max() - spec_ref_fix/spec_ref_fix.max()
            # Windowing
            wnd = sub*window
            # FFT
            fft = np.abs(np.fft.ifft(wnd, axis=0))
        
        ax0_0.set_data(wl, spec_itf)
        ax0.set_ylim((0, 1.2*spec_itf.max()))
        ax1_0.set_data(fft)
        ax1.set_ylim((0, 1.2*fft.max()))
        plt.pause(0.0001)

    p.terminate()
