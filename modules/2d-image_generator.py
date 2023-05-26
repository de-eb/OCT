from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import data_handler as dh
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt

if __name__=="__main__":
    #constants
    filename='data/2layer_cellophane_0508.csv'
    resolution=4000
    n=1.5
    depth_max=0.3
    width_h=1
    aspect=1
    vmin=0.05
    vmax=0.25

    data=dh.load_spectra(file_path=filename,wavelength_range=[770,910])
    print('<data information>\nfilename:{}\ndate:{}\nmemo:{}'.format(filename,data['date'],data['memo']))
    sp=Processor(data['wavelength'], n, depth_max, resolution)
    result_map=sp.generate_bscan(data['spectra'], data['reference'])

    plt.figure()
    plt.imshow(result_map,cmap='gray',extent=[0,depth_max*1e3,0,width_h],aspect=(depth_max*1e3/width_h)*aspect,vmin=vmin,vmax=np.amax(result_map)*vmax)
    plt.xlabel('Depth [µm]',fontsize=14)
    plt.ylabel('X [mm]',fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    plt.show()