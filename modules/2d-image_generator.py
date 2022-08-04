from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import pandas as pd
import data_handler as dh
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt

if __name__=="__main__":
    #constants
    filename='data/220803_1.csv'
    resolution=1500
    n=1.5
    depth_max=0.3
    resolution=1500
    width_h=10
    aspect=2/3

    data=dh.load_spectra(file_path=filename,wavelength_range=[770,910])
    result_map=np.zeros((len(data['spectra'][0]),resolution))
    sp=Processor(data['wavelength'], n, depth_max, resolution)
    for i in tqdm(range(len(data['spectra'][0]))):
        result_map[i]=sp.generate_ascan(data['spectra'][:,i], data['reference'])
    plt.figure()
    plt.imshow(result_map,cmap='gray',extent=[0,depth_max,0,width_h],aspect=(depth_max/width_h)*aspect,vmax=0.3)
    plt.xlabel('depth[mm]')
    plt.ylabel('width[mm]')
    plt.show()