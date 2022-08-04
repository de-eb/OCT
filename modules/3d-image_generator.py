import numpy as np
from signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from tqdm import tqdm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

if __name__=="__main__":
    #constants
    filename='data/220804_0.npz'
    resolution=400
    depth_max=0.3
    n=1.5
    st=1664
    ed=2491
    threshold=0.3

    data=np.load(filename,allow_pickle=True)
    sp=Processor(data['wavelength'][st:ed],n,depth_max,resolution)
    result_map=np.zeros((len(data['spectra']),len(data['spectra'][0]),resolution))
    w=np.linspace(0,data['width'][0],(len(data['spectra'][0])))
    h=np.linspace(0,data['height'][0],len(data['spectra']))
    d=sp.depth

    print('<data information>\ndate:{}\nmemo:{}'.format(data['date'][0],data['memo'][0]))
    for i in tqdm(range(len(data['spectra']))):
        for j in range(len(data['spectra'][0])):
            result_map[i][j]=sp.generate_ascan(data['spectra'][i][j][st:ed], data['reference'][st:ed])

    fig=plt.figure(figsize=(10,10))
    ax=fig.add_subplot(111,projection='3d')
    ax.set_xlabel("width[mm]")
    ax.set_ylabel("depth[mm]")
    ax.set_zlabel("height[mm]")    
    ax.set_xlim(0,data['width'][0])
    ax.set_ylim(0,depth_max)
    ax.set_zlim(0,data['height'][0])
    result_bin=np.array([],dtype=float)
    width=np.array([],dtype=float)
    height=np.array([],dtype=float)
    for i in tqdm(range(len(result_map))):
        for j in range(len(result_map[i])):
            target=result_map[i][j]
            for k in range(len(target)):
                if target[k]>=threshold:
                    result_bin=np.append(result_bin,d[k])
                    width=np.append(width,w[j])
                    height=np.append(height,h[i])
    
    ax.scatter(width,result_bin,height,c='blue')
    plt.show()


    
