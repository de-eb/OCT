import time
import numpy as np
import matplotlib.pyplot as plt
from modules.hp8168f import HP8168F
from modules.c10439 import C10439_11
from modules.fine01r import FINE01R

if __name__ == "__main__":

    #  Device settings
    laser = HP8168F(gpib_id='GPIB0::24::INSTR', pin=0000)  # tunable laser
    photo = C10439_11(ai_channels="Dev2/ai2")  # photo detector
    stage = FINE01R('COM5')  # piezo stage

    # Data container
    position = np.arange(start=0, stop=2000, step=10)  # stage position
    voltage = np.zeros_like(position, dtype=float)  # photo detector output

    # Measuring
    laser.output(wavelength=1500, power=200)
    stage.absolute_move(0)
    time.sleep(5)
    for i in range(len(position)):
        stage.absolute_move(position[i])
        print(stage.read_status())
        time.sleep(0.5)
        voltage[i] = np.mean(photo.read_voltage(samples=100)[1])
        print(voltage[i])
    # laser.stop()
    stage.absolute_move(0)
    
    # Save data
    data = np.vstack((position, voltage)).T
    np.savetxt('data/data.csv', data, delimiter=',')

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Measurement results")
    ax.set_xlabel("stage position [nm]")
    ax.set_ylabel("voltage [V]")
    ax.plot(position, voltage)
    plt.show()