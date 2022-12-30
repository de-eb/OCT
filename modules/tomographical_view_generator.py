import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from signal_processing_hamasaki import generate_tomographical_view
import matplotlib.pyplot as plt
import data_handler as dh
import glob

if __name__=="__main__":
    #constants
    filename='data/thin_skin_of_onion.npz'
    resolution=2000
    depth_max=0.3
    n=1.5
    st=1664
    ed=2491
    target=0.25
    vmax=0.01
    w_or_h='h' 
    aspect=2/3

    data_prepared=False

    if glob.glob(filename.strip('.npz')+'_calculated.npz'): 
        print("Calculated file confirmed.")
        c_data=np.load(file=filename.strip('.npz')+'_calculated.npz',allow_pickle=True,mmap_mode='r')
        dh.output_datainfo_calculated(c_data)
        if  c_data['depth_max'][0]==depth_max \
        and c_data['resolution'][0]==resolution \
        and c_data['n'][0]==n:
            print('Calculation conditions matched.')            
            data_prepared=True
        else:
            print('Calculation condition did not match.')

    if data_prepared is False:
        data=np.load(file=filename,allow_pickle=True,mmap_mode='r')
        sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
        dh.output_datainfo(data)
        result_all=sp.generate_cscan(data['spectra'][:,:,st:ed],data['reference'][st:ed])
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
        c_data=np.load(filename.strip('.npz')+'_calculated.npz',allow_pickle=True,mmap_mode='r')
    
    result=generate_tomographical_view(c_data,target,w_or_h)
    plt.figure()
    plt.xlabel('depth[mm]')
    if w_or_h == 'w':
        plt.imshow(result,cmap='jet',extent=[0,depth_max,0,c_data['width'][0]],aspect=(depth_max/c_data['width'][0])*aspect,vmax=vmax)
        plt.ylabel('width[mm]')
    elif w_or_h == 'h':
        plt.imshow(result,cmap='jet',extent=[0,depth_max,0,c_data['height'][0]],aspect=(depth_max/c_data['height'][0])*aspect,vmax=vmax)
        plt.ylabel('height[mm]')
    plt.show()
        