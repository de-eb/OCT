import datetime
from multiprocessing import Process, Queue
from queue import Empty
import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12, PmaError
from modules.fine01r import Fine01r
from modules.ncm6212c import Ncm6212c
from modules.artcam130mi import ArtCam130
from modules.signal_processing import SignalProcessor

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
st = 762  # Calculation range (Start) of spectrum [nm]
ed = 953  # Calculation range (End) of spectrum [nm]
g_key = None  # Pressed key


def profile_beam(q):

    camera = ArtCam130(exposure_time=2800)
    camera.open()
    while True:
        img = camera.capture(scale=0.8, grid=True)
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


def manipulate_stage(q):

    stage_m = Fine01r('COM11')  # piezo stage (mirror side)
    stage_s = Ncm6212c('COM10')  # piezo stage (sample side)
    unit = 500
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
    sp = SignalProcessor(pma.wavelength[st:ed], 1.46)
    q0 = Queue()
    q1 = Queue()
    proc0 = Process(target=manipulate_stage, args=(q0,))  # piezo stage
    proc1 = Process(target=profile_beam, args=(q1,))  # Beam profiler
    proc0.start()
    proc1.start()

    # Parameter initialization
    ref = None
    itf = np.zeros_like(pma.wavelength, dtype=float)
    err = False

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q0, q1))  # Key event
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(pma.wavelength[st:ed], itf[st:ed], label='interference')
    ax0_1, = ax0.plot(pma.wavelength[st:ed], itf[st:ed], label='reference')
    ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0, = ax1.plot(sp.depth*1e6, itf[st:ed], label='Numpy fft')
    ax1.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    
    pma.set_parameter(shutter=1)
    while g_key != 'escape':  # ESC key to exit
        # Spectral measurement
        try: itf = pma.read_spectra(averaging=5)
        except PmaError as e:
            err = True
            print(e, end="\r")
        else:
            if err:
                print("                            ", end="\r")
                err= False
        ax0_0.set_data(pma.wavelength[st:ed], itf[st:ed])  # Graph update
        ax0.set_ylim((0, 1.2*itf[st:ed].max()))

        # Signal processing
        if ref is not None:
            ascan = sp.generate_ascan(itf[st:ed], ref[st:ed])
            ax1_0.set_data(sp.depth*1e6, ascan)  # Graph update
            ax1.set_ylim((0, 0.3*ascan.max()))

        # 'Enter' key to update reference data
        if g_key == 'enter':
            ref = pma.read_spectra(averaging=100)
            sp.set_reference(ref[st:ed])
            print("Reference data updated.")
            ax0_1.set_data(pma.wavelength[st:ed], ref[st:ed])

        # 'Space' key to save data
        elif g_key == ' ':
            if ref is None:
                print("Failed to save the spectra.")
            else:
                itf = pma.read_spectra(averaging=100)  # update interference data
                with open('data/data.csv', mode='w') as f:
                    f.write('date,{}\nmemo,\n'.format(datetime.datetime.now()))
                df = pd.DataFrame(
                    data=np.vstack((pma.wavelength, np.vstack((ref, itf)))).T,
                    columns=['Wavelength [nm]', 'Reference [-]', 'Interference [-]'],
                    dtype='float')
                df.to_csv('data/data.csv', mode='a')
                print("The spectra were saved.")
        
        g_key = None
        plt.pause(0.0001)
    proc0.join()
    proc1.join()
