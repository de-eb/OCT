from signal_processing_mizobe import SignalProcessorMizobe as Processor
from signal_processing_mizobe import calculate_reflectance_2d
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

if __name__=="__main__":
    # 初期設定(OCT)
    filename_ccs = 'data/230710_RGC_focus_x6.csv'
    n , resolution , depth_max , width = 1.51 , 3000 , 0.5 , 10
    extent , aspect = [0, depth_max*1e3, 0, width] , (depth_max*1e3/width)*1              # aspect : 1の値を変えて調整可能
    vmin_oct , vmax_oct = 0.01 , 0.25
    
    # データ読み込み
    data_ccs = dh.load_spectra(file_path = filename_ccs, wavelength_range = [770, 910])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename_ccs, data_ccs['date'], data_ccs['memo']))
    sp = Processor(data_ccs['wavelength'], n, depth_max, resolution)
    b_scan = sp.generate_bscan(data_ccs['spectra'], data_ccs['reference'])
    
    
    # 初期設定(SS)
    filename_pma = 'data/230710_SS_RGC_x7_Av10.csv'
    width = 10.0                                                                          # 水平方向、垂直方向の走査幅 [mm]
    st , ed , vmin_ss, vmax_ss = 201 , 940 , 0.00 , 3.0                                   # スペクトル（CCS）の計算範囲
    
    # データ読み込み
    data_pma = dh.load_spectra(file_path = filename_pma, wavelength_range = [201,941])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename_pma, data_pma['date'], data_pma['memo']))
    wavelength, reflect, incident = data_pma['wavelength'], data_pma['spectra'], data_pma['reference']
    reflectance = calculate_reflectance_2d(reflection = reflect, incidence = incident)
    pma_st, pma_ed = Processor.find_index(wavelength, [st, ed])

    

    # グラフ表示(B-scan)
    plt.imshow(b_scan, cmap = 'jet', extent = extent, aspect = aspect, vmin = vmin_oct, vmax = np.amax(b_scan)*vmax_oct)    # cmapは jet or gist_gray
    plt.colorbar()
    plt.xlabel('Depth [µm]', fontsize = 12)
    plt.ylabel('Width [mm]', fontsize = 12)
    plt.show()
    

    # グラフ表示(ss)
    # plt.imshow(reflectance, cmap = 'jet', extent = extent, aspect = aspect, vmin = vmin, vmax = vmax)
    # plt.colorbar()
    # plt.xlabel('Wavelength [nm]', fontsize = 12)
    # plt.ylabel('Width [mm]', fontsize = 12)
    # plt.show()
    
    
    """
    # 特定の深さにおけるA-scan
    depth1, depth2 = 2000, 2500                         # depth  : resolution の範囲内
    target1 = np.zeros(b_scan.shape[0])
    target2 = np.zeros(b_scan.shape[0])
    label_d1 = 1e3*depth_max*(depth1/resolution)
    label_d2 = 1e3*depth_max*(depth2/resolution)

    for i in range(b_scan.shape[0]):
        target1[i] = b_scan[i, depth1]
        target2[i] = b_scan[i, depth2]


    # グラフ設定(B-scan + A-scan)
    plt.figure(figsize = (11,6))
    plt.subplot(1,2,1)
    plt.imshow(b_scan, cmap = 'jet', extent = extent, aspect = aspect, vmin = vmin, vmax = np.amax(b_scan)*vmax)
    plt.colorbar()
    plt.xlabel('Depth [µm]', fontsize = 12)
    plt.ylabel('Width [mm]', fontsize = 12)

    plt.subplot(1,2,2)                                              # 2次元画像のXと方向が反転して表示される
    plt.plot(target1, label = 'Depth={} [µm]'.format(label_d1))
    plt.plot(target2, label = 'Depth={} [µm]'.format(label_d2))
    plt.xlabel('Width [mm]', fontsize = 12)
    plt.ylabel('Intensity [a.u.]', fontsize = 12)
    plt.legend(loc = "upper right")
    plt.show()

    plt.plot(b_scan[0~149], label = 'A-scan')                       # b_scanは 0～149 の範囲で選択
    plt.xlabel('Depth [mm]', fontsize = 12)
    plt.ylabel('Intensity [a.u.]', fontsize = 12)
    plt.legend()
    plt.show()
    """