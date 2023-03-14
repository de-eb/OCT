import numpy as np
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import matplotlib.pyplot as plt
import modules.data_handler as dh
import glob

if __name__=="__main__":
    #calculate conditions
    filename='data/thin_skin_of_onion.npz'
    resolution=2000
    depth_max=0.3
    n=1.5
    wl_start, wl_end=770, 910

    #graph setting
    target=0.15 #[mm]
    vmax=1
    aspect=1
    mode='xy' #'xd' or 'yd' or 'xy' only
    colormap='gray' #choose from https://matplotlib.org/stable/tutorials/colors/colormaps.html

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
        st,ed=Processor.find_index(data['wavelength'],[wl_start,wl_end])
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
    
    
    plt.figure()
    plt.rcParams["figure.figsize"] = (6, 6)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    if mode == 'xd':
        plt.xlabel('Depth [mm]',fontsize=15)
        plt.ylabel('X [mm]',fontsize=15)
        result=Processor.analyze_cscan(cscan=c_data['data'],target=target,mode=mode,y_max=c_data['width'][0])
        plt.imshow(result,cmap=colormap,extent=[0,depth_max,0,c_data['width'][0]],aspect=aspect,vmax=np.amax(result)*vmax)

    elif mode == 'yd':
        plt.xlabel('Depth [mm]',fontsize=15)
        plt.ylabel('Y [mm]',fontsize=15)
        result=Processor.analyze_cscan(cscan=c_data['data'],target=target,mode=mode,y_max=c_data['height'][0])
        plt.imshow(result,cmap=colormap,extent=[0,depth_max,0,c_data['height'][0]],aspect=aspect,vmax=np.amax(result)*vmax)

    elif mode=='xy':
        plt.ylabel('X [mm]',fontsize=15)
        plt.ylabel('Y [mm]',fontsize=15)        
        result=Processor.analyze_cscan(cscan=c_data['data'],target=target,mode=mode,depth=c_data['depth'])
        plt.imshow(result,cmap=colormap,extent=[0,c_data['width'][0],0,c_data['height'][0]],aspect=aspect,vmax=np.amax(result)*vmax)

    plt.show()