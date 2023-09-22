from signal_processing_mizobe import SignalProcessorMizobe as Processor
from signal_processing_mizobe import calculate_reflectance_2d
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14

if __name__=="__main__":
    # 初期設定(OCT)
    filename_ccs = 'data/2309/230920_Roll_cellophane.csv'
    n , resolution , depth_max , width= 1.52 , 2048, 0.5 , 2.0
    vmin_oct , vmax_oct = 0.0 , 0.08
    target = 0.25                                                           # B-scanのWidthから選択
    
    # データ読み込み
    data_ccs = dh.load_spectra(file_path = filename_ccs, wavelength_range = [770, 910])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename_ccs, data_ccs['date'], data_ccs['memo']))
    sp = Processor(data_ccs['wavelength'], n, depth_max, resolution)
    
    # bscan = sp.generate_bscan(data_ccs['spectra'], data_ccs['reference'])
    # n_max = len(bscan[1]) // 4
    # bscan = sp.generate_bscan_mizobe(data_ccs['spectra'])
    # n_max = len(bscan[1]) // 4
    bscan = sp.bscan_ifft(data_ccs['spectra'], data_ccs['reference'])
    n_max = len(bscan[1]) // 8
    
    # グラフ表示(B-scan)
    extent_oct , aspect_oct = [0, depth_max*1e3, 0, width] , (depth_max*1e3/width)*1              # aspect : 1の値を変えて調整可能
    # plt.figure(tight_layout = True)
    # plt.imshow(bscan[:, :n_max], cmap = 'jet', extent = extent_oct, aspect = aspect_oct, vmin = vmin_oct, vmax = np.amax(bscan)*vmax_oct)
    # plt.colorbar()
    # plt.xlabel('Depth [µm]')
    # plt.ylabel('Width [mm]')
    # plt.show()

    # グラフ表示(B-scan & A-scan)
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplot(121, title = 'B-scan')
    plt.imshow(bscan[:, :n_max], cmap = 'jet', extent = extent_oct, aspect = aspect_oct, vmin = vmin_oct, vmax = np.amax(bscan)*vmax_oct)
    plt.colorbar()
    plt.xlabel('Depth [µm]')
    plt.ylabel('Width [mm]')
    plt.subplot(122, title = 'A-scan (Not log)')
    plt.plot(bscan[int((2.0 - target)*100),:n_max], label ='Width ={} [mm]'.format(target))
    plt.ylim(bottom = 0, top = 0.001)
    plt.xlabel('Depth [µm]')
    plt.ylabel('Intensity [-]')
    plt.legend()
    plt.show()


    # 初期設定(SS)
    filename_pma = 'data/2307/230711_RGC_SS_x6(new).csv'
    width , st , ed = 10.0 , 201 , 940                               # 水平方向、垂直方向の走査幅 [mm]
    vmin_ss , vmax_ss = 0.00 , 3.0
    
    # データ読み込み
    data_pma = dh.load_spectra(file_path = filename_pma, wavelength_range = [201,941])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename_pma, data_pma['date'], data_pma['memo']))
    wavelength, reflect, incident = data_pma['wavelength'], data_pma['spectra'], data_pma['reference']
    reflectance = calculate_reflectance_2d(reflection = reflect, incidence = incident)
    pma_st, pma_ed = Processor.find_index(wavelength, [st, ed])
    extent_ss , aspect_ss = [wavelength[pma_st], wavelength[pma_ed], 0, width] , ((abs(wavelength[pma_st] - wavelength[pma_ed]) / width))*(2/3)

    # グラフ表示(SS)
    plt.figure(tight_layout = True)
    plt.imshow(reflectance, cmap = 'jet', extent = extent_ss, aspect = aspect_ss, vmin = vmin_ss, vmax = vmax_ss)
    plt.colorbar()
    plt.xlabel('Wavelength [nm]')
    plt.ylabel('Width [mm]')
    plt.xlim(300, 900)
    plt.show()

    
    # # グラフ表示(B-scan & SS)
    # plt.figure(figsize = (12,5), tight_layout = True)
    # plt.subplot(121, title = 'B-scan')
    # plt.imshow(b_scan, cmap = 'jet', extent = extent_oct, aspect = aspect_oct, vmin = vmin_oct, vmax = np.amax(b_scan)*vmax_oct)
    # plt.colorbar(shrink = 0.45)
    # plt.xlabel('Depth [µm]')
    # plt.ylabel('Width [mm]')

    # plt.subplot(122, title = 'Reflectance')
    # plt.imshow(reflectance, cmap = 'jet', extent = extent_ss, aspect = aspect_ss, vmin = vmin_ss, vmax = vmax_ss)
    # plt.colorbar(shrink = 0.45)
    # plt.xlabel('Wavelength [nm]')
    # plt.ylabel('Width [mm]')
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