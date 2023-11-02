from signal_processing_mizobe import SignalProcessorMizobe as Processor
from signal_processing_mizobe import calculate_reflectance_2d
import data_handler as dh
import numpy as np
import pywt
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14

# ウェーブレット変換
def maddest(d, axis=None):
    return np.mean(np.absolute(d - np.mean(d, axis)), axis)

def Wavelet_transform(x, wavelet, level):
    coeff = pywt.wavedec(x, wavelet, mode="sym")
    sigma = (1/0.6745) * maddest(coeff[-level])
    uthresh = sigma * np.sqrt(2*np.log(len(x)))
    coeff[1:] = (pywt.threshold(i, value=uthresh, mode='hard') for i in coeff[1:])
    return pywt.waverec(coeff, wavelet, mode='sym'), wavelet

# 平滑フィルタ（中央値）
def Smooth_filter(data_ccs, resolution, target, n_max):
    ascan = np.zeros((len(data_ccs['spectra']), resolution))
    result = np.zeros((len(data_ccs['spectra']), resolution))
    for i in range(len(data_ccs['spectra'])):
        med = np.median(bscan[int(target), :n_max])
        avg = np.mean(bscan[int(target), :n_max])
        ascan[i] = np.where(bscan[i] < med*0.975, bscan[i]*1.025, bscan[i])
        result[i] = np.where(ascan[i] > med*0.90, ascan[i]*0.95, ascan[i])
    return result, med

if __name__=="__main__":
    # 初期設定(OCT)
    file_ccs = 'data/2310/231031_Roll_cello(4,-1)_M&I.csv'
    file_sam = 'data/2310/231031_Roll_cello(4,-1)_Sam.csv'
    n, resolution, depth_max, width, step = 1.52, 4000, 0.5, 2.0, 200
    vmin_oct , vmax_oct = -5.5 , -3.0
    point = 0.79                                                                                # Width全体の何％に該当する走査位置かを指定
    target = step*(1 - point)                                                                   # 指定した走査位置におけるA-scanを呼び出す
    extent_oct , aspect_oct = [0, depth_max*1e3, 0, width] , (depth_max*1e3/width)*1            # aspect : 1の値を変えて調整可能
    
    # データ読み込み
    data_ccs = dh.load_spectra(file_path = file_ccs, wavelength_range = [770, 910])
    data_sam = dh.load_spectra(file_path = file_sam, wavelength_range = [770, 910])
    sample = data_sam['reference']
    print('<data information>\n filename:{}\n date:{}\n memo:{}'.format(file_ccs, data_ccs['date'], data_ccs['memo']))
    sp = Processor(data_ccs['wavelength'], n, depth_max, resolution)
    # bscan = sp.bscan_ifft(data_ccs['spectra'], data_ccs['reference'])                         # 干渉光 - ミラー光
    # n_max = len(bscan[1]) // 8
    # bscan = sp.bscan_ifft_sample(data_ccs['spectra'], data_ccs['reference'], sample)          # 干渉光 - ミラー光 - 試料光
    # n_max = len(bscan[1]) // 8
    # bscan = sp.generate_bscan_mizobe(data_ccs['spectra'])                                     # 干渉光にトレンド除去
    # n_max = len(bscan[1]) // 8
    bscan = sp.bscan_trend(data_ccs['spectra'], data_ccs['reference'])
    n_max = len(bscan[1]) // 8

    # ウェーブレット変換
    result = np.zeros((len(data_ccs['spectra']), resolution))
    for i in range(len(data_ccs['spectra'])):
        result[i], wavelet = Wavelet_transform(bscan[i], wavelet='bior3.9', level=1)

    # 平滑フィルタ（中央値）
    # result = np.zeros((len(data_ccs['spectra']), resolution))
    # result, med = Smooth_filter(data_ccs, resolution, target, n_max)

    # グラフ表示(B-scan & A-scan)の原画像
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplot(121, title = 'B-scan')
    plt.imshow(bscan[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.xlabel('Depth [µm]')
    plt.ylabel('Width [mm]')
    plt.subplot(122, title = 'A-scan (Log)')
    plt.plot(bscan[int(target),:n_max], label='Width ={} [mm]'.format(width*(1-(target/150))))
    # plt.xticks((0,50,100,150,200,250), ('0','100','200','300','400','500'))                            # Resolution=4000では不要
    plt.ylim(bottom = -6.5, top = -3.0)
    plt.xlabel('Depth [µm]')
    plt.ylabel('Intensity [-]')
    plt.legend()
    plt.show()

    # グラフ表示(B-scan & A-scan)の原画像と補正画像
    plt.figure(figsize = (12,5), tight_layout = True)
    plt.subplots_adjust(wspace = 10)
    plt.subplot(221, title = 'B-scan')
    plt.imshow(bscan[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.xlabel('Depth [µm]')
    plt.ylabel('Width [mm]')
    plt.subplot(222, title = 'A-scan (Log)')
    plt.plot(bscan[int(target),:n_max], label='Width ={} [mm]'.format(width*(1-(target/150))))
    # plt.xticks((0,50,100,150,200,250), ('0','100','200','300','400','500'))
    # plt.ylim(bottom=vmin_oct, top=vmax_oct)
    plt.xlabel('Depth [µm]')
    plt.ylabel('Intensity [-]')
    plt.legend()

    plt.subplot(223, title = 'B-scan (Correction)')
    plt.imshow(result[:, :n_max], cmap='jet', extent=extent_oct, aspect=aspect_oct, vmin=vmin_oct, vmax=vmax_oct)
    plt.colorbar()
    plt.xlabel('Depth [µm]')
    plt.ylabel('Width [mm]')
    plt.subplot(224, title = 'A-scan (Correction)')
    plt.plot(result[int(target),:n_max], label="Wavelet = {}".format(wavelet))
    # plt.plot(result[int(target),:n_max], label="Median = {}".format(med))
    # plt.xticks((0,50,100,150,200,250), ('0','100','200','300','400','500'))
    # plt.ylim(bottom=vmin_oct, top=vmax_oct)
    plt.xlabel('Depth [µm]')
    plt.ylabel('Intensity [-]')
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