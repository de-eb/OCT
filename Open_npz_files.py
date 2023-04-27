import numpy as np
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import matplotlib.pyplot as plt


filename = 'data/thin_skin_of_onion_calculated.npz'
data = np.load(file = filename, allow_pickle=True)


#npzファイルの中身
print("npzファイルに含まれている各要素\n", data.files)

for i in range(len(data.files)):
    print(data.files[i], end = " ")
    # print(" 要素数:", len(data.files[i]))
    name = data.files[i]
    print("%s" % data[name])

