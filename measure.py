import time
import numpy as np
import matplotlib.pyplot as plt
from modules.c10439 import C10439_11
from modules.fine01r import FINE01R

if __name__ == "__main__":

    #  Device settings
    photo = C10439_11(ai_channels="Dev1/ai2")  # photo detector
    stage = FINE01R('COM4')  # piezo stage

    # Data container
    position = np.arange(start=0, stop=2000, step=10)  # stage position
    voltage = np.zeros_like(position, dtype=float)  # photo detector output

    # Measuring
    stage.absolute_move(0)
    time.sleep(5)
    for i in range(len(position)):
        stage.absolute_move(position[i])
        print(stage.read_status())
        time.sleep(2)
        voltage[i] = np.mean(photo.read_voltage(samples=1000)[1])
        print(voltage[i])
    
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