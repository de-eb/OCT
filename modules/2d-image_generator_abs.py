import matplotlib.pyplot as plt
import data_handler as dh
from signal_processing_hamasaki import calculate_absorbance_2d
import numpy as np

if __name__=="__main__":
    filename='data/red_cellophane_half_back_of_cover_glass_abs.csv'
    wl_st, wl_ed = 401, 910
    width=5
    aspect=1
    vmax=1.05

    data=dh.load_spectra(filename,[wl_st,wl_ed])
    print('<data information>\nfilename:{}\ndate:{}\nmemo:{}'.format(filename,data['date'],data['memo']))
    result=calculate_absorbance_2d(data['spectra'],data['reference'])

    plt.figure()
    plt.tick_params(direction='in')
    plt.imshow(result,cmap='gray',extent=[wl_st,wl_ed,0,width],aspect=(abs(wl_st-wl_ed)/width)*aspect,vmax=np.amax(result)*vmax)
    plt.xlabel('Wavelength [nm]',fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.ylabel('X [mm]',fontsize=14)
    plt.hlines(1,wl_st, wl_ed,colors='tab:blue',linewidth=2)
    plt.hlines(2.5,wl_st, wl_ed,colors='tab:orange',linewidth=2)
    plt.hlines(4,wl_st, wl_ed,colors='tab:red',linewidth=2)
    plt.subplots_adjust(bottom=0.117)
    #plt.colorbar(label='Absorbance [arb. unit]')
    plt.show()