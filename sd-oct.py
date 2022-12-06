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
#from modules.ncm6212c import Ncm6212c, Ncm6212cError
from modules.crux import Crux,CruxError
from modules.artcam130mi import ArtCam130
from modules.signal_processing_hamasaki import SignalProcessorHamasaki as Processor
from modules.signal_processing_hamasaki import calculate_absorbance 
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
    resolution=2000
    depth_max=0.3 #maximum value of depth axis[mm]
    use_um=True #whether to use [μm]　units or not
    step_h=1000 # Number of horizontal divisions
    width=20 # Horizontal scanning width[mm]
    step_v=10 # Number of vertical divisions
    height=5 # Vertical scaninng height[mm]
    memo='Sample:Thin skin of onion. lens=THORLABS 54-850'

    #Constants
    ccs_st=1664 # Calculation range (Start) of spectrum(ccs)
    ccs_ed=2491 # Calculation range (End) of spectrum(ccs)
    pl_rate=2000 # Number of pulses equals to 1mm [pulse/mm]
    pma_st=134 # calculation range(start) of spectrum(pma)
    pma_ed=953 # calculation range(end) of spectrum(pma)

    #Flag for equipment operation
    stage_s_flag=None #sample stage(Crux)
    stage_m_flag=None #reference mirror stage(fine01r)
    stage_p_flag=None #spectrometer(PMA)

    #Initial position of auto stage
    vi=0 #initial position of vertical stage
    hi=0 #initial position of horizontal stage

    # Device connection
    ccs=Ccs175m(name='USB0::0x1313::0x8087::M00801544::RAW') #Spectrometer (for OCT measurement)
    # Spectrometer (for Absorbance measurement)
    try: pma = Pma12(dev_id=5)  
    except PmaError:
        print('\033[31m'+'Error:PMA not found. Absorbance measurement function is disabled.'+'\033[0m ')
        stage_p_flag=False
    else:
        stage_p_flag=True
        
    # Piezo stage (reference mirror side)
    try: stage_m = Fine01r('COM11')  
    except Fine01rError:
        print('\033[31m'+'Error:FINE01R not found. Reference mirror movement function is disabled.'+'\033[0m ')
        stage_m_flag=False
    else:
        stage_m_flag=True
    
    # Auto stage (sample side)
    try: stage_s = Crux('COM4')  
    except CruxError:
        print('\033[31m'+'Error:Crux not found. Sample stage movement function is disabled.'+'\033[0m ')
        stage_s_flag=False
    else:
        stage_s_flag=True
        try:vi,hi = dh.load_position("modules/tools/stage_position.csv")
        except FileNotFoundError:
            print('\033[31m'+'Error:Stage position data not found.'+'\033[0m ')
        else:
            print('Stage position data loaded.')
            stage_s.biaxial_move(v=vi, vmode='a', h=hi, hmode='a')

    sp = Processor(ccs.wavelength[ccs_st:ccs_ed], n=1.5,depth_max=depth_max,resolution=resolution)
    q = Queue()
    proc1 = Process(target=profile_beam, args=(q,))  # Beam profiler
    proc1.start()
   
    #Array for OCT calculation
    reference = None  # Reference spectra
    itf = np.zeros((step_h,ccs.wavelength.size), dtype=float)  # Interference spectra
    ascan = np.zeros_like(sp.depth)
    
    #Array for Absorbance calculation
    reflect = np.zeros((step_h,pma.wavelength.size),dtype=float) #refrected light
    inc=None
    absorbance=np.zeros(pma_ed-pma_st)

    #Variables for others
    ccs_err = False
    pma_err = False
    location=np.zeros(3,dtype=int) 
    x, y, z = 100000, 0, 0  # Stage position (Initial)

    # Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', lambda event:on_key(event,q))  # Key event

    # Graph settings for　CCS Spectrometer output (for OCT measurement)
    ax0 = fig.add_subplot(221, title='Spectrometer output(CCS)', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax0.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax0.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax0_0, = ax0.plot(ccs.wavelength[ccs_st:ccs_ed], itf[0,ccs_st:ccs_ed], label='interference')
    ax0_1, = ax0.plot(ccs.wavelength[ccs_st:ccs_ed], itf[0,ccs_st:ccs_ed], label='reference')
    ax0.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)

    # Graph settings for OCT calculation result
    if use_um:
        ax1 = fig.add_subplot(223, title='A-scan', xlabel='depth [μm]', ylabel='Intensity [-]')
        ax1_0, = ax1.plot(sp.depth*1e3, ascan)
        ax1.set_xlim(0,np.amax(sp.depth)*1e3)
    else:
        ax1 = fig.add_subplot(223, title='A-scan', xlabel='depth [mm]', ylabel='Intensity [-]')
        ax1_0, = ax1.plot(sp.depth, ascan)
        ax1.set_xlim(0,np.amax(sp.depth))
    ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax1.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    # Graph settings for PMA Spectrometer  output (for Absorbance measurement)
    ax2 = fig.add_subplot(222,title='Spectrometer output(PMA)',xlabel='Wavelength [nm]',ylabel='Intensity [-]')
    ax2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax2.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax2_0,=ax2.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label='reflection')
    ax2_1,=ax2.plot(pma.wavelength[pma_st:pma_ed], reflect[0,pma_st:pma_ed]+1, label='incidence')
    ax2.legend(bbox_to_anchor=(1,1), loc='upper right', borderaxespad=0.2)
    ax2.set_yscale("log")

    # Graph settings for Absorbance calculation result
    ax3 = fig.add_subplot(224,title='Absorbance', xlabel='Wavelength [nm]')
    ax3.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax3.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    ax3_0,=ax3.plot(pma.wavelength[pma_st:pma_ed],absorbance)

    # Device initialization
    if stage_m_flag:
        stage_m.absolute_move(z)
    pma.set_parameter(shutter=1)
    ccs.set_IntegrationTime(time=0.0001)
    ccs.start_scan()

    # Main loop
    while g_key != 'escape':  # ESC key to exit
        # Spectral measurement (CCS)
        try: itf[0,:] = ccs.read_spectra(averaging=5)
        except CcsError as ccs_e:
            ccs_err = True
            print('\033[31m'+'CcsError:'+'\033[0m '+ ccs_e, end="\r")
        else:
            if ccs_err:
                print("                            ", end="\r")
                ccs_err= False
        ax0_0.set_data(ccs.wavelength[ccs_st:ccs_ed], itf[0,ccs_st:ccs_ed])  # Graph update
        ax0.set_ylim((0, 1.2*itf[0,ccs_st:ccs_ed].max()))

        # Signal processing　and plot(CCS)
        if reference is not None:
            ascan = sp.generate_ascan(itf[0,ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
            if use_um:# Graph update
                ax1_0.set_data(sp.depth*1e3, ascan)  
            else:
                ax1_0.set_data(sp.depth, ascan)
            ax1.set_ylim((0,np.amax(ascan)))

        #Spectral measurement (PMA)
        try: reflect[0,:] = pma.read_spectra(averaging=5)
        except PmaError as pma_e:
            pma_err = True
            print('\033[31m'+'PmaError:'+'\033[0m '+ pma_e, end="\r")
        else:
            if pma_err:
                print("                            ", end="\r")
                pma_err= False                   
        ax2_0.set_data(pma.wavelength[pma_st:pma_ed],reflect[0,pma_st:pma_ed])
        
        #Signal processing and plot(PMA)
        if inc is None:
            ax2.set_ylim((1,np.amax(reflect[0,pma_st:pma_ed])*1.2))
        else:
            absorbance=calculate_absorbance(reflect[0,pma_st:pma_ed], inc[pma_st:pma_ed])
            ax3_0.set_data(pma.wavelength[pma_st:pma_ed],absorbance)
            ax3.set_ylim(0,np.nanmax(absorbance))

        """-----OCT function-----"""
        # 'q' key to update reference data
        if g_key == 'q':
            reference = ccs.read_spectra(averaging=100)
            sp.set_reference(reference[ccs_st:ccs_ed])
            print("Reference data updated.")
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
        
        if g_key == 'w':  # 'w' key to save single data
            data = ccs.read_spectra(averaging=100)
            if reference is None:
                dh.save_spectra(wavelength=ccs.wavelength, spectra=data)
                print('Message:Reference data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength=ccs.wavelength, spectra=data,reference=reference)
            file_path = dh.generate_filename('png')
            plt.savefig(file_path)
            print("Saved the graph to {}.".format(file_path))

        # 'e' key to Start measurement (2-dimention data)
        elif g_key == 'e' and stage_s_flag:
            if reference is None:
                print("Error:No reference data available.")
            else:
                print("OCT:Measurement(2D) start")
                stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    itf[i,:]=ccs.read_spectra()
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.move_origin(axis_num=1,ret_form=1)
                result_map=sp.generate_bscan(itf[:,ccs_st:ccs_ed], reference[ccs_st:ccs_ed])
                plt.figure()
                plt.imshow(result_map,cmap='jet',extent=[0,depth_max,0,width],aspect=(depth_max/width)*(2/3),vmax=0.5)
                plt.colorbar()
                plt.xlabel('depth[mm]')
                plt.ylabel('width[mm]')
                # Save data
                dh.save_spectra(wavelength=ccs.wavelength, reference=reference, spectra=itf.T)
                plt.show()

        # 'r'key to start measurement(3-dimention data)
        elif g_key=='r' and stage_s_flag:
            if reference is None:
                print('Error:No reference data available.')
            else:
                print('OCT:Measurement(3D) start')
                itf_3d=np.zeros((step_v,step_h,ccs.wavelength.size),dtype=float)
                result_map=np.zeros((step_v,step_h,resolution))
                stage_s.biaxial_move(v=int(height*pl_rate/2)+vi, vmode='a', h=int((width*pl_rate/2))+hi, hmode='a')
                for i in tqdm(range(step_v)):
                    for j in range(step_h):
                        itf_3d[i][j]=ccs.read_spectra()
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v=int(height/step_v*pl_rate*(-1)), vmode='r', h=int((width*pl_rate/2)), hmode='a')
                dh.save_spectra_3d(wavelength=ccs.wavelength,width=width,height=height,reference=reference,spectra=itf_3d,memo=memo)

        #'t' key to delete reference and a-scan data       
        if g_key=='t':
            reference=None
            ax0_1.set_data(ccs.wavelength[ccs_st:ccs_ed],np.zeros(ed-st))
            ax1_0.set_data(sp.depth*1e3,np.zeros_like(sp.depth))
            print('Reference data deleted.') 

        """-----Absorbance measurement functions-----"""
        # 'a' key to update  incident light spectra data
        if g_key == 'a':
            inc = pma.read_spectra(averaging=50)
            sp.set_incidence(inc[pma_st:pma_ed])
            print('Incident light data updated.')
            ax2_1.set_data(pma.wavelength[pma_st:pma_ed],inc[pma_st:pma_ed])
            ax2.set_ylim(top=np.amax(inc)*1.2)

        # 's' key to save single data
        if g_key == 's':
            data=pma.read_spectra(averaging=100)
            if inc is None:
                dh.save_spectra(wavelength=pma.wavelength, spectra=data)
                print('Message:Incident light spectra data was not registered. Only spectra data was saved.')
            else:
                dh.save_spectra(wavelength=pma.wavelength,reference=inc,spectra=data,memo='Attention:This is absorbance measurement data.')
        
        # 'd' key to start measurement(2-dimention)
        if g_key =='d':
            if inc is None:
                print('Error:Incident light data not found.')
            else:
                print('ABS:Measurement(2D) start')
                stage_s.absolute_move(int((width*pl_rate/2)+hi))
                for i in tqdm(range(step_h)):
                    reflect[i,:]=pma.read_spectra()
                    stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                stage_s.move_origin(axis_num=1,ret_form=1)
                result_map=sp.calculate_absorbance_2d(reflection=reflect)
                plt.figure()
                plt.imshow(result_map,cmap='jet',
                extent=[pma.wavelength[pma_st],pma.wavelength[pma_ed],0,width],
                aspect=(((pma.wavelength[pma_st]-pma.wavelength[pma_ed])/width))*(2/3),
                #vmax=10
                )
                plt.colorbar()
                plt.xlabel('Wavelength[nm]')
                plt.ylabel('Width [mm]')

                #save data
                dh.save_spectra(wavelength=pma.wavelength,reference=inc,spectra=reflect.T,memo='Attention:This is absorbance measurement data.')
                plt.show()

        # 'd' key to start measurement(3-dimention)
        if g_key =='f':
            if inc is None:
                print('Error:Incident light data not found.')
            else:
                print('ABS:Measurement(3D) start')
                reflect_3d=np.zeros((step_v,step_h,pma.wavelength),dtype=float)
                stage_s.biaxial_move(v=int(height*pl_rate/2)+vi, vmode='a', h=int((width*pl_rate/2))+hi, hmode='a')
                for i in tqdm (range(step_v)):
                    for j in range(step_h):
                        reflect_3d[i][j]=pma.read_spectra()
                        stage_s.relative_move(int(width/step_h*pl_rate*(-1)))
                    stage_s.biaxial_move(v=int(height/step_v*pl_rate*(-1)), vmode='r', h=int((width*pl_rate/2)), hmode='a')
                dh.save_spectra_3d(wavelength=ccs.wavelength,width=width,height=height,reference=reference,spectra=itf_3d,memo=memo+'Attention:This is absorbance measurement data.')


        """-----Auto stage control function-----"""
        if g_key in ['4','6','5','2','8']:
            if g_key=='6':stage_s.relative_move(2000,axis_num=1,velocity=9)
            elif g_key=='4':stage_s.relative_move(-2000,axis_num=1,velocity=9)
            elif g_key=='5':
                if hi==0 and vi==0:
                    stage_s.move_origin()
                else:
                    stage_s.biaxial_move(v=vi, vmode='a', h=hi, hmode='a')
            elif g_key=='2':stage_s.relative_move(2000,axis_num=2,velocity=9)
            elif g_key=='8':stage_s.relative_move(-2000,axis_num=2,velocity=9)
            location[0]=stage_s.read_position(axis_num=1)
            location[1]=stage_s.read_position(axis_num=2)
            print('Stage position:x={}[mm],y={}[mm],z={}[nm]'.format((location[0]-hi)/pl_rate,(location[1]-vi)/pl_rate,location[2]/pl_rate))
        
        #'/' key to move the stage to the left edge (for when change sample)
        if g_key=='/': 
            stage_s.absolute_move(-71000)

        g_key = None
        plt.pause(0.0001)
    proc1.join()