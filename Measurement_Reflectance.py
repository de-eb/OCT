import time
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import modules.data_handler as dh
from modules.pma12 import Pma12,PmaError
from modules.crux import Crux,CruxError
from modules.signal_processing_hamasaki import calculate_reflectance, calculate_reflectance_2d
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from multiprocessing import Process, Queue
import warnings

# グラフ設定
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams["xtick.minor.visible"] = True
plt.rcParams["ytick.minor.visible"] = True
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams["xtick.minor.width"] = 0.5
plt.rcParams["ytick.minor.width"] = 0.5
plt.rcParams['font.size'] = 14
plt.rcParams['axes.linewidth'] = 1.0

q = Queue()
g_key = None

def on_key(event,q):
    global g_key
    g_key = event.key
    q.put(g_key)


if __name__ == "__main__":
    # パラメーターの初期設定
    step_h, step_v = 150, 150                               # 水平方向、垂直方向の分割数
    width, height = 10.0, 0.5                                # 水平方向、垂直方向の走査幅 [mm]
    averaging = 1                                           # １点の測定の平均回数
    st, ed = 201, 941                                       # スペクトル（CCS）の計算範囲
    pl_rate = 2000                                          # 1mmに相当するパルス数［pulse/mm］
    memo = '2layer cellophanes behind the cover glass(Res.=5000, Ave.=20). lens=THORLABS LSM54-850'

    # 自動ステージの設定
    stage_s_flag = None
    vi, hi = 0, 0                                           # 垂直方向のステージの初期位置
    location = np.zeros(3, dtype = int) 
    x, y, z = 100000, 0, 0


    # 使用機器
    try: stage_s = Crux('COM6')                             # 自動ステージ（試料ミラー側）
    except CruxError:
        print('\033[31m'+'Error:Crux not found. Sample stage movement function is disabled.'+'\033[0m ')
        stage_s_flag = False
    else:
        stage_s_flag = True
        try:vi,hi = dh.load_position("modules/tools/stage_position.csv")
        except FileNotFoundError:
            print('\033[31m'+'Error:Stage position data not found.'+'\033[0m ')
        else:
            print('Stage position data loaded.')
            stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')
    
    pma = Pma12(dev_id = 5)                                 # PMA（ハロゲンランプ分光器）
    pma_st, pma_ed = Processor.find_index(pma.wavelength, [st, ed])
    incident = None
    reflect = np.zeros((step_h, pma.wavelength.size),dtype=float)
    reflectance = np.zeros(pma_ed - pma_st)
    pma_err = False
    pma.set_parameter(shutter = 1)


    # グラフ設定
    fig = plt.figure(figsize = (10, 10), dpi = 80, tight_layout = True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))

    ax0 = fig.add_subplot(211, title = 'Spectrometer output', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax0.ticklabel_format(style = "sci", axis = "y",scilimits = (0,0))
    ax0_0, = ax0.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label = 'Reflected light') 
    ax0_1, = ax0.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label = 'Incident light')
    ax0.legend(bbox_to_anchor = (1,1), loc = 'upper right', borderaxespad = 0.2)
    ax0.set_yscale("log")
    ax0.set_xlim(350, 900)

    ax1 = fig.add_subplot(212, title = 'Reflectance', xlabel = 'Wavelength [mm]', ylabel = 'Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax1.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
    ax1_0, = ax1.plot(pma.wavelength[pma_st:pma_ed], reflectance) 
    warnings.simplefilter(action = 'ignore', category = UserWarning)
    ax1.set_xlim(350, 900)


    # メインループ（分光測定）
    while g_key != 'escape':
        
         # 自動ステージ（試料ステージ）の位置調整
        if g_key in ['4','6','5','2','8']:
            if g_key == '6':stage_s.relative_move(2000, axis_num = 1, velocity = 9)           # ６：右方向に1mm移動
            elif g_key == '4':stage_s.relative_move(-2000, axis_num = 1, velocity = 9)        # ４：左方向に1mm移動
            elif g_key == '5':                                                                # ５：ステージの初期位置に移動
                if hi == 0 and vi == 0:
                    stage_s.move_origin()
                else:
                    stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')
            elif g_key == '2':stage_s.relative_move(2000, axis_num = 2, velocity = 9)         # ２：上方向に1mm移動
            elif g_key == '8':stage_s.relative_move(-2000, axis_num = 2, velocity = 9)        # ８：下方向に1mm移動
            location[0] = stage_s.read_position(axis_num = 1)
            location[1] = stage_s.read_position(axis_num = 2)
            print('CRUX stage position : x={}[mm], y={}[mm], z={}[mm]'.format((location[0]-hi)/pl_rate,(location[1]-vi)/pl_rate,location[2]/pl_rate))
        
        # PMAによるスペクトル測定
        try : reflect[0, :] = pma.read_spectra(averaging = 5)
        except PmaError as e:
            pma_err = True
            print(e, end="\r")
        else:
            if pma_err:
                print("                            ", end="\r")
                pma_err = False
        ax0_0.set_data(pma.wavelength[pma_st:pma_ed], reflect[0, pma_st:pma_ed]) #changed

        # 信号処理
        if incident is None:
            ax0.set_ylim(1, np.amax(reflect)*1.2)
        else:
            reflectance = calculate_reflectance(reflect[0, pma_st:pma_ed], incident[pma_st:pma_ed]) #changed
            ax1_0.set_data(pma.wavelength[pma_st:pma_ed], reflectance) #changed
            ax1.set_ylim(0, np.nanmax(reflectance)*1.2)

        # 'Enter'キーでリファレンスを登録する
        if g_key == 'enter':
            incident = pma.read_spectra(averaging = 50)
            ax0_1.set_data(pma.wavelength[pma_st:pma_ed], incident[pma_st:pma_ed]) #changed
            ax0.set_ylim(0, np.amax(incident)*1.2) 
            print("Incident light spectra updated.")
        
        # 'Alt'キーでリファレンスのデータを保存する
        if g_key == 'alt':
            reflect = pma.read_spectra(averaging = 100)
            if incident is None:
                print('Error:Incidence light data is not registered.')
            else:
                dh.save_spectra(pma.wavelength, incident, reflect, memo='Attention:This is transmittance measurement data.')
        
        # 'Delete'キーでリファレンスのデータを削除する
        if g_key == 'delete':
            incident = None
            ax0_1.set_data(pma.wavelength[pma_st:pma_ed], np.zeros_like(pma.wavelength[pma_st:pma_ed])) #changed
            ax1_0.set_data(pma.wavelength[pma_st:pma_ed], np.zeros_like(pma.wavelength[pma_st:pma_ed])) #changed
            print('Incident data daleted.')
        
        # 'd'キーで測定開始（2次元のデータ）
        if g_key == 'd' and stage_s_flag:
            if incident is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else: 
                    print('Error:Incident light data not found.')
            else:
                print('REF : Measurement(2D) start')
                # stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    reflect[i,:] = pma.read_spectra(averaging = averaging)
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.move_origin(axis_num = 1, ret_form = 1)

                dh.save_spectra(wavelength = pma.wavelength, reference = incident, spectra = reflect.T, memo = 'Attention:This is reflectance measurement data.'+memo)

                # 反射率の計算
                result_map = calculate_reflectance_2d(reflection = reflect[:,pma_st:pma_ed], incidence = incident[pma_st:pma_ed])
                plt.figure()
                plt.imshow(result_map, cmap = 'jet', extent = [pma.wavelength[pma_st], pma.wavelength[pma_ed], 0, width],
                aspect = ((abs(pma.wavelength[pma_st] - pma.wavelength[pma_ed]) / width))*(2/3))
                plt.colorbar()
                plt.xlabel('Wavelength [nm]')
                plt.ylabel('Width [mm]')

                plt.show()
        
        g_key = None
        plt.pause(0.0001)