import sys
import time
import datetime
from multiprocessing import Process, Queue
import numpy as np
import cv2
import pandas as pd
from scipy import special, interpolate
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.pma12 import Pma12
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
            print("The image has been saved.")

    camera.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    # multiprocess
    q = Queue()
    p = Process(target=profile_beam, args=(q, 0.8, 1000))
    p.start()

    fig = plt.figure()
    ax = fig.add_subplot(111, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    spect = Pma12(dev_id=5)  # Device settings
    data = np.zeros_like(spect.wavelength, dtype=float)  # Data container

    # Measure & plot
    graph, = ax.plot(spect.wavelength, data)
    spect.set_parameter(shutter=1)
    while True:
        data = spect.read_spectra(correction=False)
        graph.set_data(spect.wavelength, data)
        ax.set_ylim((0, 1.2*data.max()))
        plt.pause(0.0001)

        key = q.get()
        if key == 27:  # ESC key to exit
            break

    p.terminate()
