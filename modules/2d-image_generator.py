from signal_processing_mizobe import SignalProcessorMizobe as Processor
from signal_processing_mizobe import calculate_reflectance_2d
import data_handler as dh
import numpy as np
import pandas as pd
import pywt
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14

def maddest(d, axis=None):
    return np.mean(np.absolute(d - np.mean(d, axis)), axis)
def Wavelet_transform(x, wavelet, level):
    coeff = pywt.wavedec(x, wavelet, mode="sym")
    sigma = (1/0.6745) * maddest(coeff[-level])
    uthresh = sigma * np.sqrt(2*np.log(len(x)))
    coeff[1:] = (pywt.threshold(i, value=uthresh, mode='hard') for i in coeff[1:])
    return pywt.waverec(coeff, wavelet, mode='sym'), wavelet

def Median_filter(bscan, target, n_max):
    ascan = np.zeros_like(bscan)
    result = np.zeros_like(bscan)
    for i in range(len(bscan)):
        med = np.median(bscan[i,:n_max])
        ascan[i] = np.where(bscan[i] < med*0.95, bscan[i]*1.025, bscan[i])
        result[i] = np.where(ascan[i] > med*0.95, ascan[i]*0.975, ascan[i])
    med = np.median(bscan[int(target),:n_max])
    print('Median value = {}'.format(med))
    return result, med

def Noise_removal(data_ccs, noise, resolution):
    itf = data_ccs['spectra']
    itf_new = np.zeros_like(itf)
    result = np.zeros((len(data_ccs['spectra']), resolution))
    for i in range(len(data_ccs['spectra'])):
        itf_new[i] = np.where(itf[i] < noise[i], 0, itf[i])
    result = sp.bscan_ifft(itf_new, data_ccs['reference'])
    return result

if __name__=="__main__":
    # 初期設定(OCT)
    file_ccs = 'data/2312/231208_Curve_cello_2.csv'
    file_sam = 'data/231120_No_smaple.csv'
    n, resolution, depth_max, width, step = 1.52, 4000, 0.5, 3.0, 100
    vmin_oct , vmax_oct = -60 , -20
    target = step*(1 - 0.66)                                                                    # 指定した走査位置におけるA-scanを呼び出す
    extent_oct , aspect_oct = [0, depth_max*1e3, 0, width] , (depth_max*1e3/width)*1            # aspect : 1の値を変えて調整可能
    
    # データ読み込み
    data_ccs = dh.load_spectra(file_path = file_ccs, wavelength_range = [770, 910])
    data_sam = dh.load_spectra(file_path = file_sam, wavelength_range = [770, 910])
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(file_ccs, data_ccs['date'], data_ccs['memo']))
    sp = Processor(data_ccs['wavelength'], n, depth_max, resolution)
    bscan = sp.bscan_ifft(data_ccs['spectra'], data_ccs['reference'])                                    # IFFT (干渉光 - ミラー)
    # bscan = sp.bscan_ifft_noise(data_ccs['spectra'], data_ccs['reference'], data_sam['spectra'])         # IFFT (干渉光 - ミラー - ノイズ)
    n_max = len(bscan[1]) // 8

    # ノイズ処理
    result = np.zeros((len(bscan), resolution))
    for i in range(len(bscan)):
        result[i] = np.convolve(bscan[i], np.ones(9)/9, mode='same')                          # 移動平均
        # result[i], wavelet = Wavelet_transform(bscan[i], wavelet='bior3.9', level=1)          # ウェーブレット変換
    # result, med = Median_filter(bscan, target, n_max)                                         # 平滑フィルタ
    # result = Noise_removal(data_ccs, data_sam['spectra'], resolution)                         # 光学系ノイズ除去
    
    # グラフ表示(B-scan & A-scan)の原画像
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplot(121, title = 'B-scan', xlabel='Depth [µm]', ylabel='Width [mm]')
    plt.imshow(bscan[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.subplot(122, title = 'A-scan (Log)', xlabel='Depth [µm]', ylabel='Intensity [-]')
    plt.plot(bscan[int(target),:n_max], label='Width ={} [mm]'.format(width*(1-(target/step))))
    plt.xticks((0,100,200,300,400,500), ('0','100','200','300','400','500'))
    plt.ylim(bottom = vmin_oct, top = vmax_oct)
    plt.legend()
    plt.show()

    # グラフ表示(B-scan & A-scan)の原画像と補正画像
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplots_adjust(wspace = 10)
    plt.subplot(221, title = 'B-scan', xlabel='Depth [µm]', ylabel='Width [mm]')
    plt.imshow(bscan[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.subplot(222, title = 'A-scan (Log)', xlabel='Depth [µm]', ylabel='Intensity [-]')
    plt.plot(bscan[int(target),:n_max], label='Width ={} [mm]'.format(width*(1-(target/step))))
    plt.xticks((0,300,600,900,1200,1500), ('0','100','200','300','400','500'))
    plt.ylim(bottom=vmin_oct, top=vmax_oct)
    plt.legend()

    plt.subplot(223, title = 'B-scan (Correction)', xlabel='Depth [µm]', ylabel='Width [mm]')
    plt.imshow(result[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.subplot(224, title = 'A-scan (Correction)', xlabel='Depth [µm]', ylabel='Intensity [-]')
    plt.plot(result[int(target),:n_max], label="Noise reduction")
    plt.xticks((0,300,600,900,1200,1500), ('0','100','200','300','400','500'))
    plt.ylim(bottom=vmin_oct, top=vmax_oct)
    plt.legend()
    plt.show()

"""""
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
    plt.imshow(reflectance, cmap='jet', extent=extent_ss, aspect=aspect_ss, vmin=vmin_ss, vmax=vmax_ss)
    plt.colorbar()
    plt.xlabel('Wavelength [nm]')
    plt.ylabel('Width [mm]')
    plt.xlim(300, 900)
    plt.show()

    # グラフ表示(B-scan & SS)
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplot(121, title = 'B-scan')
    plt.imshow(bscan, cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.xlabel('Depth [µm]')
    plt.ylabel('Width [mm]')

    plt.subplot(122, title = 'Reflectance')
    plt.imshow(reflectance, cmap='jet', extent=extent_ss, aspect=aspect_ss, vmin=vmin_ss, vmax=vmax_ss)
    plt.colorbar()
    plt.xlabel('Wavelength [nm]')
    plt.ylabel('Width [mm]')
    plt.show()
"""