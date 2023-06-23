from signal_processing_mizobe import SignalProcessorMizobe as Processor
import data_handler as dh
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

if __name__=="__main__":
    # 初期設定
    filename = 'data/230424_Redcellophane_behind_glass_1.csv'
    resolution = 5000
    n = 1.46
    depth_max = 0.5
    width_h = 1
    aspect = 1
    vmin = 0.01
    vmax = 0.12
    depth = 3000                       # depthの値は 0～5999 の範囲で選択

    # データ読み込み
    data = dh.load_spectra(file_path = filename,wavelength_range = [770,910])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(filename,data['date'],data['memo']))
    sp = Processor(data['wavelength'], n, depth_max, resolution)
    b_scan = sp.generate_bscan(data['spectra'], data['reference'])

    # 特定の深さにおけるA-scan
    target = np.zeros(b_scan.shape[0])
    label_d = 1e3*depth_max*(depth/6000)

    for i in range(b_scan.shape[0]):
        target[i] = b_scan[i, depth]


    # グラフ設定
    plt.subplot(1,2,1)
    plt.imshow(b_scan, cmap='gist_gray', extent=[0,depth_max*1e3,0,width_h], aspect=(depth_max*1e3/width_h)*aspect, vmin=vmin, vmax=np.amax(b_scan)*vmax)
    plt.xlabel('Depth [µm]', fontsize = 12)
    plt.ylabel('X [mm]', fontsize = 12)

    plt.subplot(1,2,2)                                  # 2次元画像のXと方向が反転して表示される
    plt.plot(target, label = label_d)
    plt.xlabel('X [mm]', fontsize = 12)
    plt.ylabel('Intensity [a.u.]', fontsize = 12)

    # plt.plot(b_scan[0~149], label = 'A-scan')         # b_scanは 0～149 の範囲で選択
    # plt.xlabel('Depth [mm]', fontsize = 12)
    # plt.ylabel('Intensity [a.u.]', fontsize = 12)
    plt.legend()
    plt.show()