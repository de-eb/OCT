from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import data_handler as dh
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt

if __name__=="__main__":
    #constants
    filename='data/221213_1.csv'
    resolution=2000
    n=1.5
    depth_max=0.25
    resolution=1500
    width_h=1
    aspect=2/3
    vmax=0.05

    data=dh.load_spectra(file_path=filename,wavelength_range=[770,910])
    print('<data information>')
    print('filename:',filename)
    print('date:',data['date'])
    print('memo:',data['memo'])
    sp=Processor(data['wavelength'], n, depth_max, resolution)
    result_map=sp.generate_bscan(data['spectra'], data['reference'])

    plt.figure()
    plt.imshow(result_map,cmap='jet',extent=[0,depth_max,0,width_h],aspect=(depth_max/width_h)*aspect,vmax=vmax)
    plt.xlabel('depth[mm]')
    plt.ylabel('width[mm]')
    plt.show()