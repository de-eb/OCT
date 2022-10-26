from matplotlib.colors import Colormap
import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from signal_processing_hamasaki import generate_cross_section
from tqdm import tqdm
import matplotlib.pyplot as plt
import data_handler as dh
import glob

if __name__== "__main__":
    #constants
    filename='data/220804_0.npz'
    resolution=2000
    depth_max=0.25
    n=1.5
    st=1664
    ed=2491
    target_depth=183

    process_completed=False

    if glob.glob(filename.strip('.npz')+'_calculated.npz'): 
        print("Calculated file confirmed.")
        founddata=np.load(file=filename.strip('.npz')+'_calculated.npz',allow_pickle=True)
        if founddata['depth_max'][0]==depth_max \
        and founddata['resolution'][0]==resolution \
        and founddata['n'][0]==n:
            print('Calculation conditions matched.')
            dh.output_datainfo(founddata)
            cs_map=generate_cross_section(founddata['data'],target_depth, founddata['depth'])
            w=founddata['width'][0]
            h=founddata['height'][0]
            process_completed=True
        else:
            print('Calculation condition did not matched.')
    if process_completed is False:
        data=np.load(file=filename,allow_pickle=True)
        sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
        dh.output_datainfo(data)
        result_all=sp.generate_cscan(data['spectra'][:,:,st:ed],data['reference'][st:ed])
        cs_map=generate_cross_section(result_all,target_depth,sp.depth)
        w=data['width'][0]
        h=data['height'][0]

        np.savez_compressed(filename.strip('.npz')+'_calculated.npz',
        data=result_all,
        date=data['date'],
        memo=data['memo'],
        resolution=np.array([resolution],dtype=int),
        n=np.array([n],dtype=float),
        depth_max=np.array([depth_max],dtype=float),
        depth=sp.depth,
        width=data['width'],
        height=data['height']
        )
        print('Calculation result saved.')
    
    #grath drawing
    plt.xlabel("width[mm]",fontsize=15)
    plt.ylabel('height[mm]',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.imshow(cs_map,extent=[0,w,0,h],vmax=0.04)
    plt.colorbar()
    plt.show()