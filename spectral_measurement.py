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
    stage1 = FINE01R('COM6')  # piezo stage (mirror side)
    stage2 = NCM6212C('COM7')  # piezo stage (sample side)

    # Data container
    freq = np.arange(start=190349.2, stop=199733.5, step=10)  # frequency
    # volt = np.zeros_like(freq, dtype=float)  # photo detector output
    volt = np.zeros((len(freq),1000))

    # Initializing
    laser.output(power=3000)
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)
    time.sleep(5)

    # Measuring
    for j in range(volt.shape[1]):
        for i in range(len(freq)):
            laser.set_frequency(freq[i])
            stat = laser.read_status()
            # freq[i] = stat['frequency']
            volt[i,j] = np.mean(photo.read_voltage(samples=100)[1])
            print('{:.1f} GHz, {:.3f} V'.format(freq[i],volt[i,j]))
    laser.stop()

    # Save data
    # data = np.vstack((freq, volt)).T
    data = np.hstack((np.reshape(freq, (len(freq),1)), volt))
    np.savetxt('data/data.csv', data, delimiter=',')

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Measurement results")
    ax.set_xlabel("frequency [THz]")
    ax.set_ylabel("voltage [V]")
    ax.scatter(freq*1e-3, np.mean(volt, axis=1), s=10, label='measured')
    ax.legend()
    plt.show()