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
from modules.signal_processor import SignalProcessor, DataHandler
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
g_key = None  # Pressed key


def profile_beam(q):

    camera = ArtCam130(exposure_time=2800, scale=0.8)
    camera.open()
    while True:
        img = camera.capture(grid=True)
        cv2.imshow('capture', img)
        cv2.waitKey(1)
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key == 'alt':  # 'Alt' key to save image
                cv2.imwrite('data/image.png', img)
                print("The image was saved.")
            elif key == 'escape':  # ESC key to exit
                break
    camera.close()
    cv2.destroyAllWindows()


def on_key(event, q):
    global g_key
    g_key = event.key
    q.put(g_key)


if __name__ == "__main__":
    #Constants
    st = 762  # Calculation range (Start) of spectrum [nm]
    ed = 953  # Calculation range (End) of spectrum [nm]


    # Device settings
    stage_m = Fine01r('COM11')  # Piezo stage (reference mirror side)
    stage_s = Ncm6212c('COM10')  # Piezo stage (sample side)
    pma = Pma12(dev_id=5)  # Spectrometer
    sp = SignalProcessor(pma.wavelength[st:ed], 1.0)
    dh = DataHandler()
    q = Queue()
    proc1 = Process(target=profile_beam, args=(q,))  # Beam profiler
    proc1.start()

    # Parameter initialization
    step = 1000  # Stage operation interval [nm]
    limit = 300000  # Stage operation limit [nm]
    x, y, z = 0, 0, 0  # Stage position
    ref = None  # Reference spectra
    itf = np.zeros((pma.wavelength.size, 1), dtype=float)  # Interference spectra
    ascan = np.zeros_like(sp.depth)
    err = False

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))  # Key event
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(pma.wavelength[st:ed], itf[st:ed,0], label='interference')
    ax0_1, = ax0.plot(pma.wavelength[st:ed], itf[st:ed,0], label='reference')
    ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0, = ax1.plot(sp.depth*1e6, ascan, label='Numpy fft')
    ax1.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    
    # Device initialization
    stage_m.absolute_move(z)
    stage_s.absolute_move(axis='A', position=x)
    stage_s.absolute_move(axis='B', position=y)
    pma.set_parameter(shutter=1)

    # Main loop
    while g_key != 'escape':  # ESC key to exit

        # Manual operation of Piezo stages
        if g_key in ['8', '2', '6', '4', '+', '-', '5', '0']:
            # Sample
            if g_key == '8': y += 100*step  # Up
            elif g_key == '2': y -= 100*step  # Down
            elif g_key == '6': x += 100*step  # Right
            elif g_key == '4': x -= 100*step  # Left
            elif g_key == '5': x, y = 0, 0  # Return to origin
            # Reference mirror
            elif g_key == '-': z -= 100*step  # Backward
            elif g_key == '+': z += 100*step  # Forward
            elif g_key == '0': z = 0  # Return to origin
            # Drive
            stage_m.absolute_move(z)
            stage_s.absolute_move('A', x)
            stage_s.absolute_move('B', y)
            print("Stage position [nm]: x={},y={},z={}".format(x,y,z))

        # Spectral measurement
        try: itf[:,0] = pma.read_spectra(averaging=5)
        except PmaError as e:
            err = True
            print(e, end="\r")
        else:
            if err:
                print("                            ", end="\r")
                err= False
        ax0_0.set_data(pma.wavelength[st:ed], itf[st:ed,0])  # Graph update
        ax0.set_ylim((0, 1.2*itf[st:ed,0].max()))

        # Signal processing
        if ref is not None:
            ascan = sp.generate_ascan(itf[st:ed,0], ref[st:ed])
            ax1_0.set_data(sp.depth*1e6, ascan)  # Graph update
            ax1.set_ylim((0, 0.3*ascan.max()))

        # 'Enter' key to update reference data
        if g_key == 'enter':
            ref = pma.read_spectra(averaging=100)
            sp.set_reference(ref[st:ed])
            print("Reference data updated.")
            ax0_1.set_data(pma.wavelength[st:ed], ref[st:ed])
        
        if g_key == 'alt':  # 'Alt' key to save single data
            data = pma.read_spectra(averaging=100)
            dh.save_spectra(wavelength=pma.wavelength, spectra=data)
            plt.savefig('data/graph.png')

        # 'Space' key to Start measurement
        elif g_key == ' ':
            if ref is None:
                print("No reference data available.")
            else:
                print("Measurement start.")
                for i in range(itf.shape[1]):
                    print("Stage position [nm]: x={}".format(x))
                    itf[:,i] = pma.read_spectra(averaging=5)  # update interference data
                    x += step
                    stage_s.absolute_move('A', x)
                print("Measurement complete.")

                # Save data
                dh.save_spectra(wavelength=pma.wavelength, reference=ref, spectra=itf)

        g_key = None
        plt.pause(0.0001)
    proc1.join()
