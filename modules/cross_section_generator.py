import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from tqdm import tqdm
import matplotlib.pyplot as plt

def find_index(depth,target)->int:
    array=depth*1e3
    if np.amax(array)<target or np.amin(array)>target:
        print('Error:Target is not included in depth array.')
        return 0
    else:
        for i in range(len(array)):
            print(array[i])
            if array[i]>=target:
                index=i
                break
        return index

if __name__== "__main__":
    #constants
    filename='data/220804_0.npz'
    resolution=100
    depth_max=0.3
    n=1.5
    st=1664
    ed=2491
    target_depth=140

    #data loading
    data=np.load(filename,allow_pickle=True)
    sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
    result_all=np.zeros((len(data['spectra']),len(data['spectra'][0]),resolution))
    print('<data information>\ndate:{}\nmemo:{}'.format(data['date'][0],data['memo'][0]))
    #signal processing
    for i in tqdm(range(len(data['spectra']))):
        for j in range(len(data['spectra'][0])):
            result_all[i][j]=sp.generate_ascan(data['spectra'][i][j][st:ed], data['reference'][st:ed])
    
    cs_map=np.zeros((len(data['spectra'][0]),len(data['spectra'])))
    target_index=find_index(sp.depth,target_depth)
    print(target_index)
    for i in range(len(cs_map)):
        for j in range(len(cs_map[i])):
            print(result_all[i][j][target_index])
            cs_map[i][j]=result_all[i][j][target_index]
    
    plt.imshow(cs_map)
    plt.show()