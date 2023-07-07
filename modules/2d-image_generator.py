from signal_processing_mizobe import SignalProcessorMizobe as Processor
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

if __name__=="__main__":
    # 初期設定
    filename = 'data/230703_2LC_Ref_410_(glass_basis).csv'

    n, resolution, depth_max, width_h = 1.52, 5000, 0.5, 10

    extent, aspect = [0, depth_max*1e3, 0, width_h], (depth_max*1e3/width_h)*1          # aspect : 1の値を変えて調整可能
    vmin, vmax, depth1, depth2 = 0.00, 0.50, 2000, 2500                                 # depth  : resolution の範囲内 

    # データ読み込み
    data = dh.load_spectra(file_path = filename,wavelength_range = [770,910])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename,data['date'],data['memo']))
    sp = Processor(data['wavelength'], n, depth_max, resolution)
    b_scan = sp.generate_bscan(data['spectra'], data['reference'])


    # グラフ表示(B-scan)
    plt.imshow(b_scan, cmap = 'jet', extent = extent, aspect = aspect, vmin = vmin, vmax = np.amax(b_scan)*vmax)    # cmapは jet or gist_gray
    plt.colorbar()
    plt.xlabel('Depth [µm]', fontsize = 12)
    plt.ylabel('Width [mm]', fontsize = 12)
    plt.show()
    
    
    
    """
    # 特定の深さにおけるA-scan
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