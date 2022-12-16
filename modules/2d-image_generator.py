from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import data_handler as dh
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt

if __name__=="__main__":
    #constants
    filename='data/221216_4.csv'
    resolution=4000
    n=1.5
    depth_max=0.275
    width_h=1
    aspect=2/3
    vmax=0.01

    data=dh.load_spectra(file_path=filename,wavelength_range=[770,910])
    print('<data information>\nfilename:{}\ndate:{}\nmemo:{}'.format(filename,data['date'],data['memo']))
    sp=Processor(data['wavelength'], n, depth_max, resolution)
    result_map=sp.generate_bscan(data['spectra'], data['reference'])

    plt.figure()
    plt.imshow(result_map,cmap='jet',extent=[0,depth_max,0,width_h],aspect=(depth_max/width_h)*aspect,vmax=vmax)
    plt.xlabel('depth[mm]')
    plt.ylabel('width[mm]')
    plt.show()