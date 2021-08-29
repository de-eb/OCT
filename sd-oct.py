import datetime
from multiprocessing import Process, Queue
from operator import is_
from queue import Empty
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

# Globals
c = 2.99792458e8  # Speed of light in a vacuum [m/sec].
n = 1.4  # Refractive index of the sample. cellulose = 1.46
alpha = 1.5  # Design factor of Kaiser window
st = 762  # Calculation range (Start) of spectrum [nm]
ed = 953  # Calculation range (End) of spectrum [nm]
g_key = None  # Pressed key


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
        cv2.waitKey(1)
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key == ' ':  # 'Space' key to save image
                cv2.imwrite('data/image.png', img)
                print("The image was saved.")
            elif key == 'escape':  # ESC key to exit
                break
    camera.close()
    cv2.destroyAllWindows()


def manipulate_stage(q, unit):

    stage_m = Fine01r('COM11')  # piezo stage (mirror side)
    stage_s = Ncm6212c('COM10')  # piezo stage (sample side)
    x, y, z = 0, 0, 0
    stage_m.absolute_move(z)
    stage_s.absolute_move(axis='A', position=x)
    stage_s.absolute_move(axis='B', position=y)
    
    while True:
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key in ['up', 'down', 'right', 'left', 'o', 'p', '0']:
                if key == 'up': y += unit
                elif key == 'down': y -= unit
                elif key == 'right': x += unit
                elif key == 'left': x -= unit
                elif key == 'o': z -= unit
                elif key == 'p': z += unit
                elif key == '0': x, y, z = 0, 0, 0
                stage_m.absolute_move(z)
                stage_s.absolute_move(axis='A', position=x)
                stage_s.absolute_move(axis='B', position=y)
                print("Stage position [nm]: x={},y={},z={}".format(x,y,z))
            elif key == 'escape':
                break


def on_key(event, q0, q1):
    global g_key
    g_key = event.key
    q0.put(g_key)
    q1.put(g_key)


if __name__ == "__main__":

    # Device settings
    pma = Pma12(dev_id=5)  # Spectrometer
    q0 = Queue()
    q1 = Queue()
    proc0 = Process(target=manipulate_stage, args=(q0, 500))  # piezo stage
    proc1 = Process(target=profile_beam, args=(q1, 0.8, 1000))  # Beam profiler
    proc0.start()
    proc1.start()

    # Parameter initialization
    spec_ref = None
    spec_itf = np.zeros_like(pma.wavelength, dtype=float)
    err = False
    wl = pma.wavelength[st:ed]
    n = len(wl)
    i = np.arange(n)
    s = (n-1)/(wl.max()-wl.min()) * (1/(1/wl.max()+i/(n-1)*(1/wl.min()-1/wl.max())) - wl.min())
    wl_fix = wl.min() + s*(wl.max()-wl.min())/(n-1)  # Fixed Wavelength
    x = np.linspace(0, n, n)
    window = special.iv(0, np.pi*alpha*np.sqrt(1-(2*x/len(x)-1)**2)) / special.iv(0, np.pi*alpha)  # Kaiser window
    depth = np.linspace(0, ed-st-1, ed-st)

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q0, q1))  # Key event
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(wl, spec_itf[st:ed], label='interference')
    ax0_1, = ax0.plot(wl, spec_itf[st:ed], label='reference')
    ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    ax1 = fig.add_subplot(212, title='A-scan', xlabel='data num.[-]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0, = ax1.plot(depth, spec_itf[st:ed], label='Numpy fft')
    ax1.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    
    pma.set_parameter(shutter=1)
    while g_key != 'escape':  # ESC key to exit
        # Spectral measurement
        try: spec_itf = pma.read_spectra(averaging=1)
        except PmaError as e:
            err = True
            print(e, end="\r")
        else:
            if err:
                print("                            ")
                err= False
        ax0_0.set_data(pma.wavelength[st:ed], spec_itf[st:ed])  # Graph update
        ax0.set_ylim((0, 1.2*spec_itf[st:ed].max()))

        # Signal processing
        if spec_ref is not None:
            func_itf = interpolate.interp1d(wl, spec_itf[st:ed], kind='cubic')
            spec_itf_fix = func_itf(wl_fix)  # Interpolation
            sub = spec_itf_fix/spec_itf_fix.max() - spec_ref_fix/spec_ref_fix.max()  # Normalize
            wnd = sub*window  # Windowing
            fft = np.abs(np.fft.ifft(wnd, axis=0))  # FFT
            ax1_0.set_data(depth, fft)  # Graph update
            ax1.set_ylim((0, 1.2*fft.max()))

        # 'Enter' key to update reference data
        if g_key == 'enter':
            spec_ref = pma.read_spectra(averaging=100)
            func_ref = interpolate.interp1d(wl, spec_ref[st:ed], kind='cubic')
            spec_ref_fix = func_ref(wl_fix)
            print("Reference data updated.")
            ax0_1.set_data(wl, spec_ref[st:ed])

        # 'Space' key to save data
        elif g_key == ' ':
            if spec_ref is None:
                print("Failed to save the spectra.")
            else:
                spec_itf = pma.read_spectra(averaging=100)  # update interference data
                with open('data/data.csv', mode='w') as f:
                    f.write('date,{}\nmemo,\n'.format(datetime.datetime.now().isoformat()))
                df = pd.DataFrame(
                    data=np.vstack((pma.wavelength, np.vstack((spec_ref, spec_itf)))).T,
                    columns=['Wavelength [nm]', 'Reference [-]', 'Interference [-]'],
                    dtype='float')
                df.to_csv('data/data.csv', mode='a')
                print("The spectra were saved.")
        
        g_key = None
        plt.pause(0.0001)
    proc0.join()   
    proc1.join()
