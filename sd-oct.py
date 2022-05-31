import time
from multiprocessing import Process, Queue
from queue import Empty
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12, PmaError
from modules.fine01r import Fine01r, Fine01rError
from modules.ncm6212c import Ncm6212c, Ncm6212cError
from modules.artcam130mi import ArtCam130
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import modules.data_handler as dh

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

    camera = ArtCam130(exposure_time=1000, scale=0.8, auto_iris=0)
    camera.open()
    while True:
        img = camera.capture(grid=True)
        cv2.imshow('capture', img)
        cv2.waitKey(1)
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key == 'alt':  # 'Alt' key to save image
                file_path = dh.generate_filename('jpg')
                cv2.imwrite(file_path, img)
                print("Saved the image to {}.".format(file_path))
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
    st = 762  # Calculation range (Start) of spectrum
    ed = 953  # Calculation range (End) of spectrum

    #Flag for equipment operation
    stage_s_flag=None
    stage_m_flag=None

    # Device settings
    try: stage_m = Fine01r('COM11')  # Piezo stage (reference mirror side)
    except Fine01rError:
        print('Error:FINE01R not found.Reference mirror movement function is disabled.')
        stage_m_flag=False
    else:
        stage_m_flag=True
    try: stage_s = Ncm6212c('COM10')  # Piezo stage (sample side)
    except Ncm6212cError:
        print("Error:NCM6212C not found. Sample stage movement function is disabled.")
        stage_s_flag=False
    else:
        stage_s_flag=True
    pma = Pma12(dev_id=5)  # Spectrometer
    sp = Processor(pma.wavelength[st:ed], n=1.0,depth_max=0.2,resolution=400)
    q = Queue()
    proc1 = Process(target=profile_beam, args=(q,))  # Beam profiler
    proc1.start()

    # Parameter initialization
    step = 1000  # Stage operation interval [nm]
    limit = 300000  # Stage operation limit [nm]
    x, y, z = 100000, 0, 0  # Stage position (Initial)
    ref = None  # Reference spectra
    itf = np.zeros((pma.wavelength.size, int((limit-x)/step)), dtype=float)  # Interference spectra
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
    ax1.set_xlim(0,np.amax(sp.depth)*1e6)
    # Device initialization
    if stage_m_flag:
        stage_m.absolute_move(z)
    if stage_s_flag:
        stage_s.absolute_move(axis='A', position=x)
        stage_s.absolute_move(axis='B', position=y)
    pma.set_parameter(shutter=1)

    # Main loop
    while g_key != 'escape':  # ESC key to exit

        # Manual operation of Piezo stages
        if g_key in ['8', '2', '6', '4', '+', '-', '5', '0']:
            # Sample
            if g_key == '8': y += step  # Up
            elif g_key == '2': y -= step  # Down
            elif g_key == '6': x += step  # Right
            elif g_key == '4': x -= step  # Left
            elif g_key == '5': x, y = 100000, 0  # Return to origin
            # Reference mirror
            elif g_key == '-': z -= step  # Backward
            elif g_key == '+': z += step  # Forward
            elif g_key == '0': z = 0  # Return to origin
            # Drive
            if stage_m_flag:
                stage_m.absolute_move(z)
            if stage_s_flag:
                print(stage_s.absolute_move('A', x))
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
            ax1.set_ylim((0,1))

        # 'Enter' key to update reference data
        if g_key == 'enter':
            ref = pma.read_spectra(averaging=100)
            sp.set_reference(ref[st:ed])
            print("Reference data updated.")
            ax0_1.set_data(pma.wavelength[st:ed], ref[st:ed])
        
        if g_key == 'alt':  # 'Alt' key to save single data
            data = pma.read_spectra(averaging=100)
            dh.save_spectra(wavelength=pma.wavelength, spectra=data)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))

        # 'Space' key to Start measurement
        elif g_key == ' ' and stage_s_flag:
            if ref is None:
                print("No reference data available.")
            else:
                x = 100000
                print("Measurement start.")
                for i in range(itf.shape[1]):
                    stage_s.absolute_move('A', x)
                    print("Stage position [nm]: x={}".format(x))
                    x += step
                    time.sleep(0.1)
                    itf[:,i] = pma.read_spectra(averaging=10)  # update interference data
                x = 100000
                stage_s.absolute_move('A', x)
                print("Measurement complete.")

                # Save data
                dh.save_spectra(wavelength=pma.wavelength, reference=ref, spectra=itf)

        g_key = None
        plt.pause(0.0001)
    proc1.join()
