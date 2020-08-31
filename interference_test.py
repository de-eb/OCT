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
    position = np.arange(start=0, stop=2000, step=10)  # stage position
    voltage = np.zeros_like(position, dtype=float)  # photo detector output

    # Initializing
    laser.output(wavelength=1500, power=3000)
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)
    time.sleep(5)

    # Measuring
    for i in range(len(position)):
        # Be sure to comment out one or the other.
        # stage1.absolute_move(position[i])
        stage2.absolute_move(axis='A', position=position[i])

        voltage[i] = np.mean(photo.read_voltage(samples=1000)[1])
        print('{} nm, {:.3f} V'.format(position[i],voltage[i]))
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)

    # Save data
    data = np.vstack((position, voltage)).T
    np.savetxt('data/data.csv', data, delimiter=',')

    # Calculate theoretical curve
    ref = (np.cos(2*np.pi*(position-position[np.argmax(voltage)])/1500))**2
    ref = ref * (np.max(voltage)-np.min(voltage)) + np.min(voltage)

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Measurement results")
    ax.set_xlabel("stage position [nm]")
    ax.set_ylabel("voltage [V]")
    ax.scatter(position, voltage, s=20, label='measured')
    ax.plot(position, ref, label='theoretical')
    ax.legend()
    plt.show()
