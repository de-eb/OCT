import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from tqdm import tqdm
import matplotlib.pyplot as plt
import glob

def find_index(depth,target)->int:
    array=depth*1e3
    if np.amax(array)<target or np.amin(array)>target:
        print('Error:Target is not included in depth array.')
        return 0
    else:
        for i in range(len(array)):
            if array[i]>=target:
                index=i
                break
        return index

def generate_CrossSection(data,index):
    result=np.zeros((len(data[0]),len(data)))
    for i in range(len(result)):
        for j in range(len(result[i])):
            result[i][j]=data[i][j][index]
    return result

if __name__== "__main__":
    #constants
    filename='data/220804_0.npz'
    resolution=100
    depth_max=0.3
    n=1.5
    st=1664
    ed=2491
    target_depth=205

    process_flag=False

    if glob.glob(pathname=filename.strip('.npz')+'_calculated.npz'):
        print("Calculated file confirmed.")
        founddata=np.load(file=filename.strip('.npz')+'_calculated.npz',allow_pickle=True)
        if founddata['depth_max'][0]==depth_max \
        and founddata['resolution'][0]==resolution \
        and founddata['n'][0]==n:
            print('Calculation conditions matched.')
            print('<data information>\ndate:{}\nmemo:{}'.format(founddata['date'][0],founddata['memo'][0]))
            target_index=find_index(founddata['depth'], target_depth)
            cs_map=generate_CrossSection(founddata['data'],target_index)
            process_flag=True
        else:
            print('Calculation condition did not matched.')
    if process_flag is not True:
        data=np.load(filename,allow_pickle=True)
        sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
        result_all=np.zeros((len(data['spectra']),len(data['spectra'][0]),resolution))
        print('<data information>\ndate:{}\nmemo:{}'.format(data['date'][0],data['memo'][0]))
        for i in tqdm(range(len(data['spectra']))):
            for j in range(len(data['spectra'][0])):
                result_all[i][j]=sp.generate_ascan(data['spectra'][i][j][st:ed], data['reference'][st:ed])
        target_index=find_index(sp.depth,target_depth)
        cs_map=generate_CrossSection(result_all, target_index)

        np.savez_compressed(filename.strip('.npz')+'_calculated.npz',
        data=result_all,
        date=data['date'],
        memo=data['memo'],
        resolution=np.array([resolution],dtype=int),
        n=np.array([n],dtype=float),
        depth_max=np.array([depth_max],dtype=float),
        depth=sp.depth
        )

    plt.imshow(cs_map)
    plt.show()