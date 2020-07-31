import time
import numpy as np
from modules.c10439 import C10439_11
from modules.fine01r import FINE01R

if __name__ == "__main__":

    photo = C10439_11(ai_channels="Dev1/ai2")  # initialize photo detector
    stage = FINE01R('COM4')  # initialize piezo stage

    data = np.zeros((2,100))

    for i in range(data.shape[1]):
        stage.absolute_move(i)
        print(stage.read_status())
        time.sleep(1)
        data[0,i] = i  # stage position
        tmp = photo.read_voltage(samples=100)[1]
        data[1,i] = np.mean(tmp)
        print(data[1,i])
    
    photo.stop_measuring()
    np.savetxt('data.csv', data.T, delimiter=',')