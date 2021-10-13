import time
import atexit
import numpy as np
import nidaqmx

class C10439_11:
    """ Class to control photodetector (C10439-11) by NIDAQ devices.
    """

    def __init__(self, ai_channels: str):
        """ Initiates and unlocks communication with the device.

        Parameters
        ----------
        ai_channels : `str`, required
            The port on the DAQ device where the photo detector is connected.
        """
        self.__task = nidaqmx.Task()
        self.__task.ai_channels.add_ai_voltage_chan(ai_channels)
        self.__task.start()
        # Register the exit process
        atexit.register(self.stop_measuring)
        print("C10439-11 is ready.")
    
    def read_voltage(self, samples=1):
        """ Reads the output voltage of a photodetector.

        Parameters
        ----------
        samples : `int`
            Number of data to be acquired.

        Returns
        -------
        data : `1d-ndarray`
            Output voltage [V] of photodetector.
        """
        if samples <= 1:
            return self.__task.read()
        data = np.zeros((1,samples))
        start_time = time.time()
        for i in range(samples):
            data[0,i] = self.__task.read()
        return data
    
    def stop_measuring(self):
        """ Stop the measurement and release the device.
        """
        self.__task.stop()
        self.__task.close()


if __name__ == "__main__":

    import datetime
    import pandas
    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter

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

    # Initialize DAQMX(A/D convertor) tasks.
    pd = C10439_11(ai_channels="Dev1/ai2")
    data = np.zeros((2,100))  # photodetector output (time, voltage)
    key = None  # Pressed key

    def on_key(event):
        global key
        key = event.key

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', on_key)  # Key event
    ax = fig.add_subplot(111, title='Photodetector output', xlabel='Time [sec]', ylabel='Voltage [V]')
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    graph, = ax.plot(data[0], data[1])

    start = time.time()
    while key != 'escape':  # ESC key to exit
        # Measure
        data[0,0] = time.time() - start
        data[1,0] = pd.read_voltage()
        data = np.roll(data, -1, axis=1)
        # plot
        graph.set_data(data[0], data[1])
        ax.set_xlim((data[0].min(), data[0].max()))
        ax.set_ylim((0, 1.2*data[1].max()))

        if key == ' ':  # 'Space' key to save data
            with open('data/data.csv', mode='w') as f:
                f.write('date,{}\nmemo,\n'.format(datetime.datetime.now()))
            df = pandas.DataFrame(
                data=data.T,
                columns=['Time [sec]', 'Voltage [V]'],
                dtype='float')
            df.to_csv('data/data.csv', mode='a')
            print("The data were saved.")
        
        key = None
        plt.pause(0.0001)
