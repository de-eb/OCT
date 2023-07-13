import time
from tqdm import tqdm
import cv2
import numpy as np
import modules.data_handler as dh
from queue import Empty
from multiprocessing import Process, Queue
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from modules.artcam130mi import ArtCam130
from modules.crux import Crux,CruxError
from modules.fine01r import Fine01r, Fine01rError
from modules.pma12 import Pma12, PmaError
from modules.ccs175m import Ccs175m,CcsError
from modules.signal_processing_mizobe import SignalProcessorMizobe as Processor
from modules.signal_processing_mizobe import calculate_reflectance, calculate_reflectance_2d
import warnings

# グラフ設定
plt.rcParams['font.family'] = "Times New Roman"
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

# Globals
g_key = None
def profile_beam(q):                        # CCDカメラで光軸の確認

    camera = ArtCam130(exposure_time = 500, scale = 0.8, auto_iris = 0)
    camera.open()
    while True:
        img = camera.capture(grid = True)
        cv2.imshow('capture', img)
        cv2.waitKey(1)
        try: key = q.get(block = False)
        except Empty: pass
        else:
            if key == 'alt':                # 'Alt' キーで画像を保存
                file_path = dh.generate_filename('jpg')
                cv2.imwrite(file_path, img)
                print("Saved the image to {}.".format(file_path))
            elif key == 'escape':           # 'ESC' キーで終了
                break
    camera.close()
    cv2.destroyAllWindows()

def on_key(event, q):
    global g_key
    g_key = event.key
    q.put(g_key)

if __name__ == "__main__":
    # パラメーターの初期設定
    resolution = 3000                           # 計算結果の解像度（A-scanの結果を何分割して計算するか）    最適な深さ方向の分割数は？
    depth_max = 0.5                             # 深さ方向の最大値 [mm]
    use_um = True                               # 単位 [μm] を適用するかどうか
    averaging = 1                               # １点の平均測定回数（分光測定）
    width = 10                                  # 水平方向の走査幅 [mm]
    step_h = 100                                # 水平方向の分割数
    height = 10                                 # 垂直方向の走査幅 [mm]
    step_v = 10                                 # 垂直方向の分割数
    memo = 'red cellophane and blue cellophane. lens=THORLABS 54-850, averaging=1, width=15mm, step_h=2000' 

    # 分光器の設定
    pl_rate = 2000                              # 1mmに相当するパルス数［pulse/mm］
    ccs_wl_st, ccs_wl_ed = 770, 910             # スペクトル（CCS）の計算範囲
    pma_wl_st, pma_wl_ed = 300, 910             # スペクトル（PMA）の計算範囲

    # ステージの設定
    stage_s_flag = None                         # 試料ステージ(Crux)
    stage_m_flag = None                         # ミラーステージ(fine01r)
    vi, hi = 0, 0                               # 垂直方向と水平方向のステージの初期位置
    location = np.zeros(3, dtype = int) 
    x, y, z = 100000, 0, 0

    # 使用機器の設定
    try: stage_m = Fine01r('COM8')              # ピエゾステージ（参照ミラー側）
    except Fine01rError:
        print('\033[31m'+'Error:FINE01R not found. Reference mirror movement function is disabled.'+'\033[0m ')
        stage_m_flag = False
    else:
        stage_m_flag = True
    
    try: stage_s = Crux('COM6')                 # 自動ステージ　（試料ミラー側）
    except CruxError:
        print('\033[31m'+'Error:Crux not found. Sample stage movement function is disabled.'+'\033[0m ')
        stage_s_flag = False
    else:
        stage_s_flag = True
        try: vi, hi = dh.load_position("modules/tools/stage_position.csv")
        except FileNotFoundError:
            print('\033[31m'+'Error:Stage position data not found.'+'\033[0m ')
        else:
            print('Stage position data loaded.')
            stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')

    ccs = Ccs175m(name = 'USB0::0x1313::0x8087::M00801544::RAW')                      # 分光器(OCT測定)
    ccs_st, ccs_ed = Processor.find_index(ccs.wavelength, [ccs_wl_st, ccs_wl_ed])
    pma = Pma12(dev_id = 5)                                                           # 分光器(反射率測定)
    pma_st, pma_ed = Processor.find_index(pma.wavelength, [pma_wl_st, pma_wl_ed])

    sp = Processor(ccs.wavelength[ccs_st:ccs_ed], n = 1.5, depth_max = depth_max, resolution = resolution)
    q = Queue()
    proc1 = Process(target = profile_beam, args = (q,))
    proc1.start()

    # OCTの計算に用いる変数
    reference = None                                                        # 干渉光をリファレンスに登録
    itf = np.zeros((step_h,ccs.wavelength.size), dtype = float)             # シフトした干渉光を登録
    ascan = np.zeros_like(sp.depth)
    ccs_err = False

    # 反射率の計算に用いる変数
    incident = None
    reflect = np.zeros((step_h,pma.wavelength.size), dtype = float)         # リファレンスを登録
    reflectance = np.zeros(pma_ed - pma_st)
    pma_err = False

    # グラフの初期設定（参照光と干渉光のグラフ、A-scan結果のグラフ）
    fig = plt.figure(figsize = (10, 10), dpi = 80, tight_layout = True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))
    ax0 = fig.add_subplot(221, title = 'Spectrometer output(CCS)', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax0.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
    ax0_0, = ax0.plot(ccs.wavelength[ccs_st:ccs_ed], itf[0,ccs_st:ccs_ed], label = 'Interference')
    ax0_1, = ax0.plot(ccs.wavelength[ccs_st:ccs_ed], itf[0,ccs_st:ccs_ed], label = 'Reference')
    ax0.legend(bbox_to_anchor = (1,1), loc = 'upper right', borderaxespad = 0.2)

    if use_um:
        ax1 = fig.add_subplot(223, title = 'A-scan', xlabel = 'depth [μm]', ylabel = 'Intensity [-]')
        ax1_0, = ax1.plot(sp.depth*1e3, ascan)
        ax1.set_xlim(0,np.amax(sp.depth)*1e3)
    else:
        ax1 = fig.add_subplot(223, title = 'A-scan', xlabel = 'depth [mm]', ylabel = 'Intensity [-]')
        ax1_0, = ax1.plot(sp.depth, ascan)
        ax1.set_xlim(0,np.amax(sp.depth))
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax1.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))

    # グラフの初期設定（リファレンスと反射光のグラフ、反射率のグラフ）
    ax2 = fig.add_subplot(222,title = 'Spectrometer output(PMA)', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [a.u.]')
    ax2.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax2.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
    ax2_0,= ax2.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label = 'Reflected light')
    ax2_1,= ax2.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label = 'Incident light')
    ax2.legend(bbox_to_anchor = (1,1), loc = 'upper right', borderaxespad = 0.2)
    ax2.set_yscale("log")
    ax2.set_xlim(350, 900)

    ax3 = fig.add_subplot(224, title = 'Reflectance', xlabel = 'Wavelength [nm]', ylabel = 'Reflectance [a.u.]')
    ax3.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax3.ticklabel_format(style = "sci", axis = "y", scilimits = (0,0))
    ax3_0,= ax3.plot(pma.wavelength[pma_st:pma_ed], reflectance)
    warnings.simplefilter(action = 'ignore', category = UserWarning)
    ax3.set_xlim(350, 900)

    # 使用機器の初期設定
    if stage_m_flag:
        stage_m.absolute_move(z)
    pma.set_parameter(shutter = 1)
    ccs.set_IntegrationTime(time = 0.0001)
    ccs.start_scan()


    # メインループ
    while g_key != 'escape':

        """ ステージの操作コマンド一覧 """
        # 自動ステージ（試料ホルダー）の位置調整
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
        
        # ピエゾステージ（参照ミラー）の位置調整
        if g_key in ['7','9','1','3','0']:
            if g_key == '7':stage_m.relative_move(100)                                      # 7：前方に100nm移動
            elif g_key == '9':stage_m.relative_move(10)                                     # 9：前方に10nm移動
            elif g_key == '1':stage_m.relative_move(200)                                    # 1：前方に200nm移動
            elif g_key == '3':stage_m.relative_move(20)                                     # 3：前方に20nm移動
            elif g_key == '0':stage_m.absolute_move(0)                                      # 0：ステージの初期位置に移動
            print('FINE stage position : x={}[nm]'.format(stage_m.status['position']))
        
        # '/' キーでステージを左端に移動する（サンプル変更時用）
        if g_key=='/': 
            stage_s.absolute_move(-71000)

        
        # <リアルタイム測定：CCS>（光強度が飽和しているとエラーメッセージ）
        try: itf[0,:] = ccs.read_spectra(averaging = 5)
        except CcsError as ccs_e:
            ccs_err = True
            print(ccs_e, end = "\r")
            ax0_0.set_color('tab:red')
        else:
            if ccs_err:
                print("                                     ", end = "\r")
                ax0_0.set_color('tab:blue')
                ccs_err = False
        ax0_0.set_data(ccs.wavelength[ccs_st:ccs_ed], itf[0, ccs_st:ccs_ed])            # グラフのアップデート
        ax0.set_ylim((0, 1.2*itf[0, ccs_st:ccs_ed].max()))

        if reference is not None:
            ascan = sp.generate_ascan(itf[0,ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
            if use_um:
                ax1_0.set_data(sp.depth*1e3, ascan)  
            else:
                ax1_0.set_data(sp.depth, ascan)
            ax1.set_ylim((0,np.amax(ascan)))

        # <リアルタイム測定：PMA>（光強度が飽和しているとエラーメッセージ）
        try: reflect[0,:] = pma.read_spectra(averaging = 5)
        except PmaError as pma_e:
            pma_err = True
            print(pma_e, end = "\r")
            ax2_0.set_color('tab:red')
        else:
            if pma_err:
                print("                                     ", end = "\r")
                ax2_0.set_color('tab:blue')
                pma_err = False               
        ax2_0.set_data(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed])
        
        # 信号処理（反射率）
        if incident is not None:
            # reflectance = sp.calculate_absorbance(reflect[0, pma_st:pma_ed], incident[pma_st:pma_ed])
            reflectance = sp.calculate_reflectance(reflect[0, pma_st:pma_ed], incident[pma_st:pma_ed])
            ax3_0.set_data(pma.wavelength[pma_st:pma_ed], reflectance)
            ax3.set_ylim(0, np.nanmax(reflectance))
        

        """ OCT測定で使用するコマンド一覧 """
        if g_key == 'enter':                                # 'Enter' キーでリファレンス（干渉光）を登録する
            reference = ccs.read_spectra(averaging = 100)
            sp.set_reference(reference[ccs_st:ccs_ed])
            print("Reference data updated.")
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
        
        if g_key == 's':                                    # 's' キーでリファレンスのデータを保存する
            data = ccs.read_spectra(averaging = 100)
            if reference is None:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data)
                print('Message:Reference data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data, reference = reference)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))

        elif g_key == 'd':                                  # 'd' キーで測定開始（2次元のデータ）
            if reference is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else:
                    print("Error:No reference data available.")
            else:
                print("OCT:Measurement(2D) start")
                stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    itf[i,:] = ccs.read_spectra(averaging)
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.move_origin(axis_num = 1, ret_form = 1)
                result_map=sp.generate_bscan(itf[:,ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
                plt.figure()
                plt.imshow(result_map ,cmap = 'jet', extent = [0,depth_max,0,width], aspect = (depth_max/width)*(2/3), vmax = 0.5)
                plt.colorbar()
                plt.xlabel('depth[mm]')
                plt.ylabel('width[mm]')
                dh.save_spectra(wavelength = ccs.wavelength, reference = reference, spectra = itf.T, memo = memo)
                plt.show()

        elif g_key == 'f' and stage_s_flag:                 # 'f' キーで測定開始（3次元のデータ）
            if reference is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else:               
                    print('Error:No reference data available.')
            else:
                print('OCT:Measurement(3D) start')
                itf_3d = np.zeros((step_v, step_h, ccs.wavelength.size), dtype = float)
                result_map = np.zeros((step_v, step_h, resolution))
                stage_s.biaxial_move(v = int(height*pl_rate/2)+vi, vmode = 'a', h = int((width*pl_rate/2))+hi, hmode = 'a')
                for i in tqdm(range(step_v)):
                    for j in range(step_h):
                        itf_3d[i][j] = ccs.read_spectra(averaging)
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v = int(height/step_v*pl_rate*(-1)), vmode = 'r', h = int((width*pl_rate/2)), hmode = 'a')
                dh.save_spectra_3d(wavelength = ccs.wavelength, width = width, height = height, reference = reference, spectra = itf_3d, memo = memo)
      
        if g_key == 'a':                                    # 'a' キーでリファレンスとa-scanのデータを削除する  
            reference = None
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed], np.zeros(ccs_ed - ccs_st))
            ax1_0.set_data(sp.depth*1e3, np.zeros_like(sp.depth))
            print('Reference data deleted.') 


        """ 反射率測定で使用するコマンド一覧 """
        if g_key == 'alt':                                  # 'Alt' キーでリファレンスのデータを登録する
            incident = pma.read_spectra(averaging = 50)
            sp.set_incidence(incident[pma_st:pma_ed])
            print('Incident light data updated.')
            ax2_1.set_data(pma.wavelength[pma_st:pma_ed], incident[pma_st:pma_ed])

        if g_key == 'x':                                    # 'x' キーでリファレンスのデータを保存する
            data=pma.read_spectra(averaging = 100)
            if incident is None:
                dh.save_spectra(wavelength = pma.wavelength, spectra = data)
                print('Message:Incident light spectra data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength = pma.wavelength, reference = incident, spectra = data, memo = 'Attention:This is absorbance measurement data.')
        
        if g_key =='c' and stage_s_flag:                    # 'c' キーで測定開始（2次元のデータ）
            if incident is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else: 
                    print('Error:Incident light data not found.')
            else:
                print('REF:Measurement(2D) start')
                stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    reflect[i,:] = pma.read_spectra(averaging = averaging)
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.move_origin(axis_num = 1, ret_form = 1)

                dh.save_spectra(wavelength=pma.wavelength,reference=incident,spectra=reflect.T,memo='Attention:This is absorbance measurement data.'+memo)

                #signal processing and plot
                # result_map=sp.calculate_absorbance_2d(reflection=reflect[:,pma_st:pma_ed])
                result_map = sp.calculate_reflectance_2d(reflect[:,pma_st:pma_ed], incident[pma_st:pma_ed])
                plt.figure()
                plt.imshow(result_map,cmap='jet', extent=[pma.wavelength[pma_st], pma.wavelength[pma_ed],0,width], aspect=((abs(pma.wavelength[pma_st]-pma.wavelength[pma_ed])/width))*(2/3),)
                plt.colorbar()
                plt.xlabel('Wavelength [nm]')
                plt.ylabel('Width [mm]')
                plt.show()

        if g_key == 'v' and stage_s_flag:                   # 'v' キーで測定開始（3次元のデータ）
            if incident is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else: 
                    print('Error:Incident light data not found.')
            else:
                print('REF:Measurement(3D) start')
                reflect_3d = np.zeros((step_v, step_h, pma.wavelength), dtype = float)
                stage_s.biaxial_move(v = int(height*pl_rate/2)+vi, vmode = 'a', h = int((width*pl_rate/2))+hi, hmode = 'a')
                for i in tqdm (range(step_v)):
                    for j in range(step_h):
                        reflect_3d[i][j] = pma.read_spectra(averaging = averaging)
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v = int(height/step_v*pl_rate*(-1)), vmode = 'r', h = int((width*pl_rate/2)), hmode = 'a')
                dh.save_spectra_3d(wavelength=pma.wavelength, width=width, height=height, reference=incident, spectra=reflect, memo=memo+'Attention:This is absorbance measurement data.')

        if g_key == 'z':                                    # 'z' キーでリファレンスのデータを削除する
            incident = None
            ax2_1.set_data(pma.wavelength[pma_st:pma_ed], np.zeros(pma_ed-pma_st)+1)
            ax3_0.set_data(pma.wavelength[pma_st:pma_ed], np.zeros(pma_ed-pma_st))
            print('Incident light data deleted.')


        """ OCTと反射率の同時測定で使用するコマンド一覧 """
        if g_key == 'q':                                    # 'q' キーでOCTとSSのリファレンスを登録する
            incident = pma.read_spectra(averaging = 50)
            sp.set_incidence(incident[pma_st:pma_ed])
            print('Incident light data updated.')
            ax2_1.set_data(pma.wavelength[pma_st:pma_ed], incident[pma_st:pma_ed])
            reference = ccs.read_spectra(averaging = 100)
            sp.set_reference(reference[ccs_st:ccs_ed])
            print("Reference data updated.")
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
        
        if g_key == 'w':                                    # 'w' キーでリファレンスのデータを保存する
            data = ccs.read_spectra(averaging = 100)
            if reference is None:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data)
                print('Message:Reference data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data, reference = reference)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))
            data=pma.read_spectra(averaging = 100)
            if incident is None:
                dh.save_spectra(wavelength = pma.wavelength, spectra = data)
                print('Message:Incident light spectra data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength=pma.wavelength, reference=incident, spectra=data, memo='Attention:This is absorbance measurement data.')

        if g_key == 'e' and stage_s_flag:                   # 'e' キーで測定開始（2次元のデータ）
            if incident is None or reference is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else:
                    if incident is None:
                        print('Error:Incident light data not found.')      
                    if reference is None:
                        print('Error:No reference data available.')   
            else:
                print('OCT & REF:Measurement(2D) start')

                # OCT+反射率の測定ループ
                stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    reflect[i,:] = pma.read_spectra(averaging = averaging)
                    itf[i,:] = ccs.read_spectra(averaging)
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')

                # 信号処理
                result_abs = sp.calculate_absorbance_2d(reflection = reflect)
                result_oct = sp.generate_bscan(itf[:,ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
                dh.save_spectra(wavelength = pma.wavelength, reference = incident, spectra = reflect.T, memo = 'Attention:This is absorbance measurement data.')
                dh.save_spectra(wavelength = ccs.wavelength, reference = reference, spectra = itf.T)

                # グラフ出力
                plt.figure()
                plt.imshow(result_map, cmap = 'jet', extent = [0,depth_max,0,width], aspect = (depth_max/width)*(2/3), vmax = 0.5)
                plt.colorbar()
                plt.xlabel('depth[mm]')
                plt.ylabel('width[mm]')
                plt.show()
        
        if g_key == 'r':                                    # 'r' キーで測定開始（3次元のデータ）
            if incident is None or reference is None or stage_s_flag == False:
                if stage_s_flag == False:
                    print('Error:Crux is not connected.')
                else:
                    if incident is None:
                        print('Error:Incident light data not found.')      
                    if reference is None:
                        print('Error:No reference data available.')   
            else:
                print('REF:Measurement(3D) start')

                # OCT+反射率の測定ループ
                reflect_3d = np.zeros((step_v, step_h, pma.wavelength), dtype = float)
                itf_3d = np.zeros((step_v, step_h, ccs.wavelength.size), dtype = float)
                stage_s.biaxial_move(v=int(height*pl_rate/2)+vi, vmode='a', h=int((width*pl_rate/2))+hi, hmode='a')
                for i in tqdm (range(step_v)):
                    for j in range(step_h):
                        reflect_3d[i][j] = pma.read_spectra(averaging = averaging)
                        itf_3d[i][j] = ccs.read_spectra(averaging)
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v=int(height/step_v*pl_rate*(-1)), vmode='r', h=int((width*pl_rate/2)), hmode='a')
                stage_s.biaxial_move(v=vi, vmode='a', h=hi, hmode='a')

                dh.save_spectra_3d(wavelength=ccs.wavelength, width=width, height=height, reference=reference, spectra=itf_3d, memo=memo)
                dh.save_spectra_3d(wavelength=pma.wavelength, width=width, height=height, reference=incident, spectra=reflect, memo=memo+'Attention:This is absorbance measurement data.')
        
        if g_key == 't':                                    # 't' キーでOCTとSSのリファレンスデータを削除する
            reference = None
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed], np.zeros(ccs_ed-ccs_st))
            ax1_0.set_data(sp.depth*1e3, np.zeros_like(sp.depth))
            print('Reference data deleted.') 
            incident = None
            ax2_1.set_data(pma.wavelength[pma_st:pma_ed], np.zeros(pma_ed-pma_st)+1)
            ax3_0.set_data(pma.wavelength[pma_st:pma_ed], np.zeros(pma_ed-pma_st))
            print('Incident light data deleted.')            

        g_key = None
        plt.pause(0.0001)
    proc1.join()