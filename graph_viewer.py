import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

if __name__ == "__main__":

    # Data loading
    data = pd.read_csv('data/201029_1.csv', header=2, index_col=0)
    position = data.values[:,0]
    voltage = data.values[:,1]

    # Calculate theoretical curve
    ref = (np.cos(2*np.pi*(position-position[np.argmax(voltage)])/1540))**2
    ref = ref * (np.max(voltage)-np.min(voltage)) + np.min(voltage)

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Interference Fringes in the optical axis")
    ax.set_xlabel("stage position [nm]")
    ax.set_ylabel("voltage [V]")
    ax.scatter(position, voltage, s=20, label='measured')
    ax.plot(position, ref, label='theoretical')
    ax.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=1)
    plt.show()