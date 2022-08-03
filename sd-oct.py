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
from modules.ncm6212c import Ncm6212c, Ncm6212cError
from modules.crux import Crux,CruxError
from modules.artcam130mi import ArtCam130
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
import modules.data_handler as dh
from modules.ccs175m import Ccs175m,CcsError

# Graph settings
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

# Globals
g_key = None  # Pressed key


def profile_beam(q):

    camera = ArtCam130(exposure_time=500, scale=0.8, auto_iris=0)
    camera.open()
    while True:
        img = camera.capture(grid=True)
        cv2.imshow('capture', img)
        cv2.waitKey(1)
        try: key = q.get(block=False)
        except Empty: pass
        else:
            if key == 'alt':  # 'Alt' key to save image
                file_path = dh.generate_filename('jpg')
                cv2.imwrite(file_path, img)
                print("Saved the image to {}.".format(file_path))
            elif key == 'escape':  # ESC key to exit
                break
    camera.close()
    cv2.destroyAllWindows()


def on_key(event, q):
    global g_key
    g_key = event.key
    q.put(g_key)


if __name__ == "__main__":
    # Parameter initialization
    resolution=1500
    depth_max=0.4 #maximum value of depth axis[mm]
    exponentation=3
    #↑Use 3 when using [mm] for depth axis units and 6 when using [μm].
    #(Axis label automatically change according to number)
    step_h=20 # Number of horizontal divisions
    width=10 # Horizontal scanning width[mm]
    step_v=20 # Number of vertical divisions
    height=10 # Vertical scaninng height[mm]

    #Constants
    st=1664 # Calculation range (Start) of spectrum(ccs)
    ed=2491 # Calculation range (End) of spectrum(ccs)
    pl_rate=2000 # Number of pulses equals to 1mm [pulse/mm]

    #Flag for piezo stage operation
    stage_s_flag=None
    stage_m_flag=None

    # Device settings
    try: stage_m = Fine01r('COM11')  # Piezo stage (reference mirror side)
    except Fine01rError:
        print('Error:FINE01R not found.Reference mirror movement function is disabled.')
        stage_m_flag=False
    else:
        stage_m_flag=True
    try: stage_s = Crux('COM4')  # Auto stage (sample side)
    except CruxError:
        print("Error:Crux not found. Sample stage movement function is disabled.")
        stage_s_flag=False
    else:
        stage_s_flag=True
    #pma = Pma12(dev_id=5)  # Spectrometer (old)
    ccs=Ccs175m(name='USB0::0x1313::0x8087::M00801544::RAW') #Spectrometer (new)
    sp = Processor(ccs.wavelength[st:ed], n=1.5,depth_max=depth_max,resolution=resolution)
    q = Queue()
    proc1 = Process(target=profile_beam, args=(q,))  # Beam profiler
    proc1.start()
   
    #step = 1000  # Stage operation interval [nm]
    #limit = 300000  # Stage operation limit [nm]
    x, y, z = 100000, 0, 0  # Stage position (Initial)
    ref = None  # Reference spectra
    itf = np.zeros((step_h,ccs.wavelength.size), dtype=float)  # Interference spectra
    itf_3d=np.zeros((step_h,step_v,ccs.wavelength.size),dtype=float)
    ascan = np.zeros_like(sp.depth)
    err = False
    location=np.zeros(3,dtype=int)

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))  # Key event
    ax0 = fig.add_subplot(211, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(ccs.wavelength[st:ed], itf[0,st:ed], label='interference')
    ax0_1, = ax0.plot(ccs.wavelength[st:ed], itf[0,st:ed], label='reference')
    ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    if exponentation ==6:
        ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
    else:
        ax1 = fig.add_subplot(212, title='A-scan', xlabel='depth [mm]', ylabel='Intensity [-]')
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax1_0, = ax1.plot(sp.depth*(10**exponentation), ascan)
    ax1.set_xlim(0,np.amax(sp.depth)*(10**exponentation))

    # Device initialization
    if stage_m_flag:
        stage_m.absolute_move(z)
    #pma.set_parameter(shutter=1)
    ccs.set_IntegrationTime(time=0.0001)
    ccs.start_scan()
    # Main loop
    while g_key != 'escape':  # ESC key to exit
        '''
        # Manual operation of Piezo stages
        if g_key in ['8', '2', '6', '4', '+', '-', '5', '0']:
            # Sample
            if g_key == '8': y += step  # Up
            elif g_key == '2': y -= step  # Down
            elif g_key == '6': x += step  # Right
            elif g_key == '4': x -= step  # Left
            elif g_key == '5': x, y = 100000, 0  # Return to origin
            # Reference mirror
            elif g_key == '-': z -= step  # Backward
            elif g_key == '+': z += step  # Forward
            elif g_key == '0': z = 0  # Return to origin
            # Drive
            if stage_m_flag:
                stage_m.absolute_move(z)
            if stage_s_flag:
                print(stage_s.absolute_move('A', x))
                stage_s.absolute_move('B', y)
            print("Stage position [nm]: x={},y={},z={}".format(x,y,z))
        '''
        if g_key in ['4','6','5','2','8']:
            if g_key=='6':stage_s.relative_move(2000,axis_num=1,velocity=9)
            elif g_key=='4':stage_s.relative_move(-2000,axis_num=1,velocity=9)
            elif g_key=='5':
                stage_s.move_origin(axis_num=1,velocity=9)
                stage_s.move_origin(axis_num=2,velocity=9)
            elif g_key=='2':stage_s.relative_move(2000,axis_num=2,velocity=9)
            elif g_key=='8':stage_s.relative_move(-2000,axis_num=2,velocity=9)
            location[0]=stage_s.read_position(axis_num=1)
            location[1]=stage_s.read_position(axis_num=2)
            print('Stage position:x={}[mm],y={}[mm],z={}[nm]'.format(location[0]/pl_rate,location[1]/pl_rate,location[2]/pl_rate))

        # Spectral measurement
        try: itf[0,:] = ccs.read_spectra(averaging=5)
        except CcsError as e:
            err = True
            print(e, end="\r")
        else:
            if err:
                print("                            ", end="\r")
                err= False
        ax0_0.set_data(ccs.wavelength[st:ed], itf[0,st:ed])  # Graph update
        ax0.set_ylim((0, 1.2*itf[0,st:ed].max()))

        # Signal processing
        if ref is not None:
            ascan = sp.generate_ascan(itf[0,st:ed], ref[st:ed])
            ax1_0.set_data(sp.depth*(10**exponentation), ascan)  # Graph update
            ax1.set_ylim((0,np.amax(ascan)))

        #'Delete' key to delete reference and a-scan data       
        if g_key=='delete':
            ref=None
            ax0_1.set_data(ccs.wavelength[st:ed],np.zeros(ed-st))
            ax1_0.set_data(sp.depth*1e3,np.zeros_like(sp.depth))
            print('Reference data deleted.')            

        # 'Enter' key to update reference data
        if g_key == 'enter':
            ref = ccs.read_spectra(averaging=100)
            sp.set_reference(ref[st:ed])
            print("Reference data updated.")
            ax0_1.set_data(ccs.wavelength[st:ed], ref[st:ed])
        
        if g_key == 'alt':  # 'Alt' key to save single data
            data = ccs.read_spectra(averaging=100)
            if ref is None:
                dh.save_spectra(wavelength=ccs.wavelength, spectra=data)
                print('Message:Reference data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength=ccs.wavelength, spectra=data,reference=ref)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))
        
        if g_key=='/': #'/' key to move the stage to the left edge (for when change sample)
            stage_s.absolute_move(-71000)

        # 'd' key to Start measurement (2-dimention data), double
        elif g_key == 'd' and stage_s_flag:
            if ref is None:
                print("Error:No reference data available.")
            else:
                result_map=np.zeros((step_h,resolution))
                print("Measurement(2D) start")
                stage_s.absolute_move(int((width*pl_rate/2)))
                for i in tqdm(range(step_h)):
                    itf[i,:]=ccs.read_spectra()
                    result_map[i]=sp.generate_ascan(itf[i,st:ed],ref[st:ed])
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                plt.figure()
                plt.imshow(result_map,cmap='gray',extent=[0,depth_max,0,width],aspect=(depth_max/width)*(2/3),vmax=0.5)
                plt.colorbar()
                if exponentation==6:
                    plt.xlabel('depth[μm]')
                else:
                    plt.xlabel('depth[mm]')
                plt.ylabel('width[mm]')
                # Save data
                dh.save_spectra(wavelength=ccs.wavelength, reference=ref, spectra=itf.T)
                stage_s.move_origin(axis_num=1,ret_form=1)
                plt.show()
        # 't'key to start measurement(3-dimention data), triple
        elif g_key=='t' and stage_s_flag:
            if ref is None:
                print('Error:No reference data available.')
            else:
                result_map=np.zeros((step_v,step_h,resolution))
                stage_s.absolute_move(int((width*pl_rate/2)))
                stage_s.absolute_move(int(height*pl_rate/2),axis_num=2)
                for i in tqdm(range(step_v)):
                    for j in range(step_h):
                        itf_3d[i][j]=ccs.read_spectra()
                        result_map[i][j]=sp.generate_ascan(itf_3d[i][j][st:ed], ref[st:ed])
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.absolute_move(int((width*pl_rate/2)))
                    stage_s.relative_move(int(height/step_v*pl_rate*(-1)),axis_num=2)



        g_key = None
        plt.pause(0.0001)
    proc1.join()