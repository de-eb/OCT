import time
import datetime
import numpy as np
import pandas as pd
from modules.pma12 import Pma12
from modules.hp8168f import HP8168F
from modules.c10439 import C10439_11
from modules.fine01r import Fine01r
from modules.ncm6212c import Ncm6212c

if __name__ == "__main__":

    # Device settings
    spect = Pma12(dev_id=5)  # spectrometer
    stage1 = Fine01r('COM11')  # piezo stage (mirror side)
    stage2 = Ncm6212c('COM10')  # piezo stage (sample side)

    # Data container
    spectra = data = np.zeros((spect.wavelength.size,4), dtype=float)
    stage_pos = [0, 1000, 2000, 3000]

    # Initializing
    spect.set_parameter(shutter=1)
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)
    time.sleep(2)

    # Measuring
    print("Measurement start.")
    for i in range(spectra.shape[1]):
        stage1.absolute_move(position=stage_pos[i])
        time.sleep(1)
        spectra[:,i] = spect.read_spectra(averaging=100)

    # Save data
    with open('data/data.csv', mode='w') as f:
        f.write('date,{}\nmemo,\n'.format(datetime.datetime.now().isoformat()))
    data = pd.DataFrame(
        data=np.hstack((np.reshape(spect.wavelength,(spect.wavelength.size, 1)), spectra)),
        columns=['Wavelength [nm]']+['Intensity_{} [-]'.format(i) for i in range(spectra.shape[1])],
        dtype='float')
    data.to_csv('data/data.csv', mode='a')
    print("Measurement complete.")
