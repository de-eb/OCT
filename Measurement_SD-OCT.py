import time
from multiprocessing import Process, Queue
from queue import Empty
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from tqdm import tqdm
from modules.pma12 import Pma12, PmaError
from modules.fine01r import Fine01r, Fine01rError
from modules.crux import Crux,CruxError
from modules.artcam130mi import ArtCam130
from modules.signal_processing_mizobe import SignalProcessorMizobe as Processor
import modules.data_handler as dh
from modules.ccs175m import Ccs175m,CcsError
#from modules.ncm6212c import Ncm6212c, Ncm6212cError

# グラフの設定
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
g_key = None  # Pressed key

def profile_beam(q):                    # CCDカメラで光軸の確認

    camera = ArtCam130(exposure_time=500, scale=0.8, auto_iris=0)
    camera.open()
    while True:
        img = camera.capture(grid=True)
        cv2.imshow('capture', img)
        cv2.waitKey(1)
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key == 'alt':            # 'Alt' キーで画像を保存
                file_path = dh.generate_filename('jpg')
                cv2.imwrite(file_path, img)
                print("Saved the image to {}.".format(file_path))
            elif key == 'escape':       # 'ESC' キーで終了
                break
    camera.close()
    cv2.destroyAllWindows()


def on_key(event, q):
    global g_key
    g_key = event.key
    q.put(g_key)


if __name__ == "__main__":
    # パラメーターの初期設定
    resolution = 4000                 # 計算結果の解像度（A-scanの結果を何分割して計算するか）
    depth_max = 1.0                   # 深さ方向の最大値 [mm]
    use_um = True                     # 単位 [μm] を適用するかどうか
    step_h = 100                      # 水平方向の分割数（100で固定）
    width = 1.0                       # 水平方向の走査幅 [mm]
    step_v = 150                      # 垂直方向の分割数
    height = 0.5                      # 垂直方向の走査幅 [mm]
    averaging = 100                   # １点の測定の平均回数
    memo = 'Mirror(Res.=4000, Ave.=100). lens=THORLABS LSM54-850'

    # SLD光源の波長
    st = 1664                         # スペクトル（CCS）の計算範囲（開始）
    ed = 2491                         # スペクトル（CCS）の計算範囲（終了）
    pl_rate = 2000                    # 1mmに相当するパルス数［pulse/mm］

    # 自動ステージ動作用フラグ
    stage_s_flag = None
    stage_m_flag = None

    # 自動ステージの初期位置
    vi = 0                            # 垂直方向のステージの初期位置
    hi = 0                            # 水平方向のステージの初期位置

    # 使用機器の設定
    try: stage_m = Fine01r('COM8')   # ピエゾステージ（参照ミラー側）
    except Fine01rError:
        print('\033[31m'+'Error:FINE01R not found. Reference mirror movement function is disabled.'+'\033[0m ')
        stage_m_flag = False
    else:
        stage_m_flag = True
    try: stage_s = Crux('COM6')       # 自動ステージ　（試料ミラー側）
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
            stage_s.biaxial_move(v=vi, vmode='a', h = hi, hmode = 'a')
    #pma = Pma12(dev_id=5)                                                                  # 旧分光器：PMA (分光測定)
    ccs = Ccs175m(name = 'USB0::0x1313::0x8087::M00801544::RAW')                            # 新分光器：CCS (OCT測定)
    sp = Processor(ccs.wavelength[st:ed], n = 1.52, depth_max = depth_max, resolution = resolution)
    q = Queue()
    proc1 = Process(target = profile_beam, args = (q,))
    proc1.start()
   
    # step = 1000                                                                           # Stage operation interval [nm]
    # limit = 300000                                                                        # Stage operation limit [nm]
    x, y, z = 100000, 0, 0                                                                  # ステージの初期位置
    ref = None                                                                              # 参照光（リアルタイム測定用）
    rld = np.zeros((step_h, ccs.wavelength.size), dtype = float)                            # 参照光（step_h, ccs.wavelength）
    itf = np.zeros((step_h, ccs.wavelength.size), dtype = float)                            # 干渉光（step_h, ccs.wavelength）
    itf_3d = np.zeros((step_v, step_h, ccs.wavelength.size), dtype = float)                 # 干渉光（step_v, step_h, ccs.wavelength）
    ascan = np.zeros_like(sp.depth)
    err = False
    location = np.zeros(3,dtype = int)

    # グラフの初期設定（参照光と干渉光のグラフ、A-scan結果のグラフ）
    fig = plt.figure(figsize = (10, 10), dpi = 80, tight_layout = True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))                                             # Key event
    ax0 = fig.add_subplot(211, title = 'Spectrometer output', xlabel = 'Wavelength [nm]', ylabel = 'Intensity [-]')     # 参照光と干渉光
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax0.ticklabel_format(style = "sci",  axis = "y",scilimits = (0,0))
    ax0_0, = ax0.plot(ccs.wavelength[st:ed], itf[0,st:ed], label = 'Interference')                                      # 干渉光
    ax0_1, = ax0.plot(ccs.wavelength[st:ed], itf[0,st:ed], label = 'Reference')                                         # 参照光
    ax0.legend(bbox_to_anchor = (1,1), loc = 'upper right', borderaxespad = 0.2)
    if use_um:
        ax1 = fig.add_subplot(212, title = 'A-scan', xlabel = 'Depth [μm]', ylabel = 'Intensity [-]')                   # A-scanの結果
        ax1_0, = ax1.plot(sp.depth*1e3, ascan)
        ax1.set_xlim(0,np.amax(sp.depth)*1e3)
    else:
        ax1 = fig.add_subplot(212, title = 'A-scan', xlabel = 'Depth [mm]', ylabel = 'Intensity [-]')
        ax1_0, = ax1.plot(sp.depth, ascan)
        ax1.set_xlim(0,np.amax(sp.depth))
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText = True))
    ax1.ticklabel_format(style = "sci",  axis = "y",scilimits = (0,0))
    

    # 使用機器の初期設定
    if stage_m_flag:
        stage_m.absolute_move(z)
    #pma.set_parameter(shutter=1)
    ccs.set_IntegrationTime(time=0.0001)
    ccs.start_scan()


    # メインループ（SD-OCTの測定）
    while g_key != 'escape':                                                                # 'ESC' キーで終了
        
        # 自動ステージ（試料ステージ）の位置調整
        if g_key in ['4','6','5','2','8']:
            if g_key == '6':stage_s.relative_move(1000,axis_num = 1,velocity = 9)           # ６：右方向に1mm移動
            elif g_key == '4':stage_s.relative_move(-1000,axis_num = 1,velocity = 9)        # ４：左方向に1mm移動
            elif g_key == '5':                                                              # ５：ステージの初期位置に移動
                if hi == 0 and vi == 0:
                    stage_s.move_origin()
                else:
                    stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')
            elif g_key == '2':stage_s.relative_move(1000,axis_num = 2,velocity = 9)         # ２：上方向に1mm移動
            elif g_key == '8':stage_s.relative_move(-1000,axis_num = 2,velocity = 9)        # ８：下方向に1mm移動
            location[0] = stage_s.read_position(axis_num = 1)
            location[1] = stage_s.read_position(axis_num = 2)
            print("CRUX stage position : x={} [mm], y={} [mm]".format((location[0]-hi)/pl_rate, (location[1]-vi)/pl_rate))
        
        # ピエゾステージ（参照ミラー）の位置調整
        if g_key in ['7','9','1','3','0']:
            if g_key == '7':stage_m.relative_move(100)                                      # 7：前方に100nm移動
            elif g_key == '9':stage_m.relative_move(10)                                     # 9：前方に10nm移動
            elif g_key == '1':stage_m.relative_move(200)                                    # 1：前方に200nm移動
            elif g_key == '3':stage_m.relative_move(20)                                     # 3：前方に20nm移動
            elif g_key == '0':stage_m.absolute_move(0)                                      # 0：ステージの初期位置に移動
            print("FINE stage position : x={} [nm]".format(stage_m.status['position']))

        # スペクトル測定（光強度が飽和しているとエラーメッセージ）
        try: itf[0,:] = ccs.read_spectra(averaging = 5)
        except CcsError as e:
            err = True
            print(e, end = "\r")
            ax0_0.set_color('tab:red')
        else:
            if err:
                print("                            ", end = "\r")
                err= False
                ax0_0.set_color('tab:blue')
        ax0_0.set_data(ccs.wavelength[st:ed], itf[0,st:ed])                 # グラフの更新
        ax0.set_ylim((0, 1.2*itf[0,st:ed].max()))

        # 信号処理
        if ref is not None:
            # ascan = sp.generate_ascan_mizobe(itf[0,st:ed])
            ascan = sp.generate_ascan(itf[0,st:ed], ref[st:ed])
            if use_um:                                                      # グラフの更新
                ax1_0.set_data(sp.depth*1e3, ascan)                         # 距離の単位換算
            else:
                ax1_0.set_data(sp.depth, ascan)
            ax1.set_ylim((0, np.amax(ascan)))

        # 'Delete'キーでリファレンスとa-scanのデータを削除する  
        if g_key == 'delete':
            ref = None
            ax0_1.set_data(ccs.wavelength[st:ed], np.zeros(ed-st))          # 参照光のデータ
            ax1_0.set_data(sp.depth*1e3, np.zeros_like(sp.depth))           # A-scanのデータ
            print("Reference data deleted.")            

        # 'Enter'キーでリファレンス（干渉光）を登録する
        if g_key == 'enter':
            ref = ccs.read_spectra(averaging = 100)
            sp.set_reference(ref[st:ed])
            print("Reference data updated.")
            ax0_1.set_data(ccs.wavelength[st:ed], ref[st:ed])
        
        # 'Alt'キーでリファレンスのデータを保存する
        if g_key == 'alt':
            data = ccs.read_spectra(averaging = 100)
            if ref is None:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data)
                print("Message : Reference data was not registered. Only spectra data was saved.")
            else:
                dh.save_spectra(wavelength = ccs.wavelength, spectra = data, reference = ref)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))
        
        # '/' キーでステージを左端に移動する（サンプル変更時用）
        if g_key == '/':
            stage_s.absolute_move(-71000)

        # 'r'キーで参照光分布測定開始
        elif g_key == 'r' and stage_s_flag:
            start_x, start_y = stage_s.read_position(axis_num = 1), stage_s.read_position(axis_num = 2)
            print("Measurement( Reference light distribution ) start")
            for i in tqdm(range(step_h)):
                rld[i,:] = ccs.read_spectra(averaging)
                stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
            print("Reference light distribution is updated.")
            stage_s.biaxial_move(v = start_y, vmode = 'a', h = start_x, hmode = 'a')
            crux_x, crux_y = ((stage_s.read_position(axis_num = 1)) -hi)/pl_rate, ((stage_s.read_position(axis_num = 2)) -vi)/pl_rate
            print("Crux stage position : x={} [nm], y={} [mm]".format(crux_x, crux_y))

        # 'd'キーで測定開始（2次元のデータ）
        elif g_key == 'd' and stage_s_flag:
            if rld is None:
                print("Error : No reference data available.")
            else:
                print("Measurement( 2D:Interference light ) start")
                for i in tqdm(range(step_h)):
                    # itf[i,:] = ccs.read_raw_data(target=50)                             # 均等に分割された波長軸での干渉光
                    itf[i,:] = ccs.read_spectra(averaging)
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                result_map = sp.generate_bscan_mizobe(itf[:,st:ed])                     # 均等に分割された時間軸での光強度（b-scan）
                plt.figure()
                plt.imshow(result_map, cmap = 'jet', extent = [0,depth_max,0,width], aspect = (depth_max/width)*(2/3), vmin = 0.05, vmax = 0.5)
                plt.colorbar()
                plt.xlabel('Depth [mm]')
                plt.ylabel('Width [mm]')
                dh.save_spectra(wavelength = ccs.wavelength, reference = ref, spectra = itf.T, memo = memo)
                stage_s.move_origin(axis_num = 1, ret_form = 1)
                plt.show()
    
        # 't'キーで測定開始（3次元のデータ）
        elif g_key == 't' and stage_s_flag:
            if rld is None:
                print('Error : No reference data available.')
            else:
                print("Measurement( 3D:Interference light ) start")
                stage_s.biaxial_move(v=int(height*pl_rate/2)+vi, vmode = 'a', h = int((width*pl_rate/2))+hi, hmode = 'a')
                for i in tqdm(range(step_v)):
                    for j in range(step_h):
                        itf_3d[i][j] = ccs.read_spectra(averaging)
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v = int(height/step_v*pl_rate*(-1)), vmode = 'r', h = int((width*pl_rate/2)), hmode = 'a')
                # データの保存
                dh.save_spectra_3d(wavelength = ccs.wavelength, width = width, height = height, reference = rld, spectra = itf_3d, memo = memo)

        # 光源をHe-Neレーザーに設定し、測定対象範囲に光が当たるかどうかを確認する
        # 'p' キーで 2 次元測定の測定範囲を確認する
        if g_key == 'p':
            print('pre-check function called.\n<current parameter of 2D measurement>\nstaninng width:{}[mm]\nstep:{}'.format(width,step_h))
            stage_s.biaxial_move(v = vi, vmode = 'a', h = int((width*pl_rate/2)+hi), hmode = 'a')
            time.sleep(1)
            stage_s.absolute_move(position = int((-1)*(width*pl_rate/2)+hi),axis_num = 1)
            time.sleep(1)
            stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')

        # 'l' キーで 2 次元測定の測定範囲を確認する
        if g_key == 'l':
            print('pre-check function called.\n<current parameter of 2D measurement>\n \
            length horizontal:{}[mm]/vertical:{}[mm]\nstep:horizontal:{}/vertical:{}'.format(width,height,step_h,step_v))
            stage_s.biaxial_move(v = int(height*pl_rate/2)+vi, vmode = 'a', h = int((width*pl_rate/2))+hi, hmode = 'a')
            time.sleep(1)
            stage_s.biaxial_move(v = 0, vmode = 'r', h=(-1)*int((width*pl_rate/2))+hi, hmode = 'a')
            time.sleep(1)
            stage_s.biaxial_move(v=(-1)*int(height*pl_rate/2)+vi, vmode = 'a', h = int((width*pl_rate/2))+hi, hmode = 'a')
            time.sleep(1)
            stage_s.biaxial_move(v = 0, vmode = 'r', h=(-1)*int((width*pl_rate/2))+hi, hmode = 'a')
            time.sleep(1)
            stage_s.biaxial_move(v = vi, vmode = 'a', h = hi, hmode = 'a')                
        g_key = None
        plt.pause(0.0001)
    proc1.join()