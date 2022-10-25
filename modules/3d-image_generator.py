import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from tqdm import tqdm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import copy

if __name__=="__main__":
    #constants
    filename='data/220804_0.npz'
    resolution=400
    depth_max=0.3
    n=1.5
    st=1664
    ed=2491
    threshold=[0.1, 0.2, 0.4, 0.6, 0.8, 1.0]

    #data loading
    data=np.load(filename,allow_pickle=True)
    sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
    result_map=np.zeros((len(data['spectra']),len(data['spectra'][0]),resolution))
    w=np.linspace(0,data['width'][0],(len(data['spectra'][0])))
    h=np.linspace(0,data['height'][0],len(data['spectra']))
    d=sp.depth
    print('<data information>\ndate:{}\nmemo:{}'.format(data['date'][0],data['memo'][0]))

    #Signal processing
    for i in tqdm(range(len(data['spectra']))):
        for j in range(len(data['spectra'][0])):
            result_map[i][j]=sp.generate_ascan(data['spectra'][i][j][st:ed], data['reference'][st:ed])

    #graph configuration
    fig=plt.figure(figsize=(10,10))
    ax=fig.add_subplot(111,projection='3d')
    ax.set_xlabel("width[mm]")
    ax.set_ylabel("depth[mm]")
    ax.set_zlabel("height[mm]")    
    ax.set_xlim(0,data['width'][0])
    ax.set_ylim(0,depth_max)
    ax.set_zlim(0,data['height'][0])

    arr_len_max=0
    for i in tqdm(range(len(result_map))):
        for j in range(len(result_map[i])):
            arr_len=0
            for k in range(len(result_map[i][j])):
                if result_map[i][j][k]>=threshold[0]:
                    arr_len+=1
            if arr_len>arr_len_max:
                arr_len_max=arr_len

    result_bin=np.array([[np.nan]*arr_len_max]*(len(threshold)-1),dtype=float)
    width=copy.deepcopy(result_bin)
    height=copy.deepcopy(result_bin)

    for i in tqdm(range(len(result_map))):
        for j in range(len(result_map[i])):
            for k in range(len(result_map[i][j])):
                '''
                if result_map[i][j][k]>=threshold:
                    result_bin=np.append(result_bin,d[k])
                    width=np.append(width,w[j])
                    height=np.append(height,h[i])
                '''
                for l in range(len(threshold)-1):
                    if threshold[l]<=result_map[i][j][k]<threshold[l+1]:
                        for m in range(len(result_bin[l])):
                            if np.isnan(result_bin[l][m]):
                                result_bin[l][m]=d[k]
                                width[l][m]=w[j]
                                height[l][m]=h[i]
                                break


    for i in range(len(threshold)-1):
        ax.scatter(width[i],result_bin[i],height[i],label=str(i))
    plt.legend()
    plt.show()