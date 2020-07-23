import numpy as np
import matplotlib.pyplot as plt
import nidaqmx
import time

if __name__ == "__main__":

    data = np.zeros((2,100))  # photodetector output (time, voltage)

    # Initialize DAQMX(A/D convertor) tasks.
    task = nidaqmx.Task()
    task.ai_channels.add_ai_voltage_chan("Dev2/ai2")
    task.start()

    # Initialize graph.
    fig, ax = plt.subplots(1, 1)
    ax.set_ylim((0, 0.5))
    ax.set_title("photodetector output")
    ax.set_xlabel("time [sec]")
    ax.set_ylabel("voltage [V]")
    graph, = ax.plot(data[0], data[1])

    start = time.time()
    while True:
        data[0,0] = time.time() - start
        data[1,0] = task.read()
        data = np.roll(data, -1, axis=1)
        graph.set_data(data[0], data[1])
        ax.set_xlim((data[0].min(), data[0].max()))
        plt.pause(0.0001)

    task.stop()
    task.close()