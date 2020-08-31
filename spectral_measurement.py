import time
import numpy as np
import matplotlib.pyplot as plt
from modules.hp8168f import HP8168F
from modules.c10439 import C10439_11
from modules.fine01r import FINE01R
from modules.ncm6212c import NCM6212C

if __name__ == "__main__":

    # Device settings
    laser = HP8168F(gpib_id='GPIB0::24::INSTR', pin=0000)  # tunable laser
    photo = C10439_11(ai_channels="Dev1/ai2")  # photo detector
    stage1 = FINE01R('COM4')  # piezo stage (mirror side)
    stage2 = NCM6212C('COM5')  # piezo stage (sample side)

    # Data container
    wavelength = np.arange(start=1475.0, stop=1580.1, step=0.1)  # wavelength
    voltage = np.zeros_like(wavelength, dtype=float)  # photo detector output

    # Initializing
    laser.output(wavelength=1475, power=3000)
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)
    time.sleep(5)

    # Measuring
    for i in range(len(wavelength)):
        laser.output(wavelength=wavelength[i], power=250)
        stat = laser.read_status()
        voltage[i] = np.mean(photo.read_voltage(samples=100)[1])
        print('{:.3f} nm, {:.3f} V'.format(wavelength[i],voltage[i]))
    laser.stop()

    # Save data
    data = np.vstack((wavelength, voltage)).T
    np.savetxt('data/data.csv', data, delimiter=',')

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Measurement results")
    ax.set_xlabel("wavelength [nm]")
    ax.set_ylabel("voltage [V]")
    ax.scatter(wavelength, voltage, s=20, label='measured')
    ax.legend()
    plt.show()