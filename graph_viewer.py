import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":

    # Data loading
    data = np.loadtxt('data/201003_7.csv', delimiter=',')
    position = data[:,0]
    voltage = data[:,1]

    # Calculate theoretical curve
    ref = (np.cos(2*np.pi*(position-position[np.argmax(voltage)])/1540))**2
    ref = ref * (np.max(voltage)-np.min(voltage)) + np.min(voltage)

    # Show Graph
    fig, ax = plt.subplots(1, 1)
    ax.set_title("Interference fringes of Coverslip(0.148mm) at 1540nm")
    ax.set_xlabel("stage position [nm]")
    ax.set_ylabel("voltage [V]")
    ax.scatter(position, voltage, s=20, label='measured')
    ax.plot(position, ref, label='theoretical')
    ax.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=1)
    plt.show()