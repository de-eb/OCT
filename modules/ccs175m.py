import ctypes
import numpy as np
import warnings
import atexit

class CcsError(Exception):
    """ Base exception class for this modules.
    Outputs a message to the TERMINAL instead of an exception message
     because of unfixable garbled characters.

    Attributes
    ----------
    err : `int`
        Status codes that VISA driver-level operations can return. 
    session : `int`
        An instrument handle which is used in call functions.
    """
    def __init__(self,status_code:int,session:int,msg="See terminal for details."):
        self.err=status_code
        self.handle=session
        if session:
            Ccs175m.close(self.handle)
        self.msg=msg
        Ccs175m.output_ErrorMessage(self, status_code=self.err, session=self.handle)
    def __str__(self):
        return self.msg

class Ccs175m():
    """Class to control compact spectrometer(CCS175/M)
    """
    #External modules loading
    __dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

    num_pixels=3648 #number of effective pixels of CCD

    def __init__(self,name:str):
        """Initiates and unlock communication with the device

        Parameters
        ----------
        name : `str`, required
            VISA resource name of the device.

        Raise
        ---------
        CcsError :
            When the module initialization fails.
            Details are output to terminal
        """
        #device initializing
        self.__name=ctypes.create_string_buffer(name.encode('utf-8'))
        self.__handle=ctypes.c_long()
        Ccs175m.__dev.tlccs_Init.argtypes=(ctypes.c_char_p,ctypes.c_bool,ctypes.c_bool,ctypes.POINTER(ctypes.c_long))
        err=Ccs175m.__dev.tlccs_Init(self.__name,False,False,ctypes.byref(self.__handle))
        if err:
            raise CcsError(status_code=err,session=self.__handle)

        #get wavelength data
        Ccs175m.__dev.GetWavelengthDataArray.argtype=(ctypes.c_long)
        Ccs175m.__dev.GetWavelengthDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=Ccs175m.num_pixels)
        self.__wavelength=Ccs175m.__dev.GetWavelengthDataArray(self.__handle)

        #Resister the exit process
        atexit.register(self.close)

        #Set types of arguments and return value of GetScanDataArray function.
        Ccs175m.__dev.GetScanDataArray.argtype=(ctypes.c_long)
        Ccs175m.__dev.GetScanDataArray.restypes=np.ctypeslib.ndpointer(dtype=np.double,shape=Ccs175m.num_pixels)

        print("CCS175M is ready.")
    @property
    def wavelength(self):
        """Wavelength [nm] axis corresponding to the measurement data.
        """
        return self.__wavelength

    def set_IntegrationTime(self,time=0.01):
        """This function set the optical integration time in seconds.

        Parameter
        ---------
        time : `float`
            The optical integration time.
        
        Raise
        ---------
        CcsError :
            When the setting fails.
        """
        err=Ccs175m.__dev.tlccs_SetIntegrationTime(self.__handle)
        if err:
            raise CcsError(status_code=err,session=self.__handle)

    def start_scan(self):
        """This function starts the CCS scanning continuously.
        Any other function except 'read_spectra' will stop the scanning.
        """
        err=Ccs175m.__dev.tlccs_SrartScanCont(self.__handle)
        if err:
            raise CcsError(status_code=err,session=self.__handle)

    def read_spectra(self,averaging=1):
        data=np.zeros(Ccs175m.num_pixels)
        if averaging<1:
            warnings.warn('The value of averaging must always be greater than or equal to 1.')
            averaging=1
        for i in range(averaging):
            #sp=Ccs175m.__dev.GetScanDataArray(self.__handle)
            #data+=sp
            data+=Ccs175m.__dev.GetScanDataArray(self.__handle)
        return data/averaging

    def output_ErrorMessage(self,status_code:int,session:int):
        Ccs175m.__dev.OutputErrorMessage(status_code,session)

    def close(self) ->bool:
        """This function close an instrument driver session.

        Raise
        --------
        CcsError :
            When the module is not controlled correctly.
        """
        err=Ccs175m.__dev.tlccs_Close(self.handle)
        if err:
            raise CcsError(status_code=err,session=self.__handle)
        
if __name__=="__main__":
    import matplotlib.pyplot as plt
    import pandas as pd

    #Graph setting
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

    #Parameter initiallization
    ccs=Ccs175m(name='USB0::0x1313::0x8087::M00801544::RAW')
    ccs.set_IntegrationTime(7)

    key=None
    def on_key(event):
        global key
        key=event.key

    #graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', on_key)  # Key event
    ax = fig.add_subplot(111, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    graph, = ax.plot(pma.wavelength, data)    
'''
#dllファイル　ロード
dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')


#接続
name='USB0::0x1313::0x8087::M00801544::RAW'
name=ctypes.create_string_buffer(name.encode('utf-8'))
handle=ctypes.c_long()
dev.tlccs_Init.argtypes=(ctypes.c_char_p,ctypes.c_bool,ctypes.c_bool,ctypes.POINTER(ctypes.c_long))
err=dev.tlccs_Init(name,False,False,ctypes.byref(handle))

if err:
    raise CcsError(status_code=err,session=handle)

#露光時間設定
integration_time=ctypes.c_double(0.01)
err=dev.tlccs_SetIntegrationTime(handle,integration_time)
if err:
    raise CcsError(status_code=err,session=handle)

#測定開始
err=dev.tlccs_StartScan(handle.value+1)
if err:
    raise CcsError(status_code=err,session=handle)


#測定データの取得
ccs_num_pixels=3648 #number of effective pixels of CCD
dev.GetScanDataArray.argtype=(ctypes.c_long)
dev.GetScanDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=ccs_num_pixels)
sp=dev.GetScanDataArray(handle)

#波長軸データの取得
dev.GetWavelengthDataArray.argtype=(ctypes.c_long)
dev.GetWavelengthDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=ccs_num_pixels)
wl=dev.GetWavelengthDataArray(handle)

#データプロット
plt.plot(wl,sp)
plt.xlabel("wavelength[nm]",fontsize=17)
plt.ylabel("light intensity[arb. unit]",fontsize=17)
plt.show()

#セッション終了
err=dev.tlccs_Close(handle)
if err:
    raise CcsError(status_code=err,session=handle)
'''