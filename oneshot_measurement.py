import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from modules.hp8168f import HP8168F
from modules.c10439 import C10439_11
from modules.fine01r import Fine01r
from modules.ncm6212c import Ncm6212c

if __name__ == "__main__":

    # Device settings
    laser = HP8168F(gpib_id='GPIB0::24::INSTR', pin=0000)  # tunable laser
    photo = C10439_11(ai_channels="Dev1/ai2")  # photo detector
    stage1 = Fine01r('COM12')  # piezo stage (mirror side)
    stage2 = Ncm6212c('COM10')  # piezo stage (sample side)

    # Data container
    x_ax = np.arange(start=0, stop=10, step=0.1)
    y_ax = np.zeros_like(x_ax, dtype=float)

    # Initializing
    laser.set_wavelength(wavelength=1500)
    laser.output(power=3000)
    stage1.absolute_move(0)
    stage2.absolute_move(axis='A', position=0)
    stage2.absolute_move(axis='B', position=0)

    # Measuring
    try:
        for i in range(len(x_ax)):
            key = input('Press Enter to measure or Ctrl+C to exit.')
            if key == '':  # Enter
                y_ax[i] = np.mean(photo.read_voltage(samples=1000)[1])
                print('{}:, {:.3f} V'.format(x_ax[i],y_ax[i]))
    except KeyboardInterrupt:  # Ctrl + C
        laser.stop()
        photo.stop_measuring()
        stage2.absolute_move(axis='A', position=0)

    # Save data
    with open('data/data.csv', mode='w') as f:
        f.write('date,{}\nmemo,\n'.format(datetime.datetime.now().isoformat()))
    data = pd.DataFrame(
        data=np.vstack((x_ax, y_ax)).T,
        columns=['x']+['y'],
        dtype='float')
    data.to_csv('data/data.csv', mode='a')

    # Show Graph
    fig = plt.figure()
    ax = fig.add_subplot(111, title='Results', xlabel='x', ylabel='y')
    ax.scatter(x_ax, y_ax, s=5, label='measured')
    ax.legend()
    plt.show()
