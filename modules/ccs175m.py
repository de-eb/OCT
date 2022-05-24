import ctypes
import numpy as np
import warnings
import atexit
import time

class CcsError(Exception):
    """ Base exception class for this modules.
    Outputs a message to the terminal or an exception message
     because of unfixable garbled characters.

    Attributes
    ----------
    err : `int`
        Status codes that VISA driver-level operations can return. 
    session : `int`
        An instrument handle which is used in call functions.
    """
    def __init__(self,status_code:int,session:ctypes.c_long,msg="See terminal for details."):
        self.__err=ctypes.c_long(status_code)
        self.__handle=session
        #if session:
        #    Ccs175m.close_ccs(self.__handle)
        self.__msg=msg
        Ccs175m.output_ErrorMessage(self, status_code=self.__err, session=self.__handle)
        print('(Error code:',self.__err.value,')')
    def __str__(self):
        return self.__msg

class Ccs175m():
    """Class to control compact spectrometer(CCS175/M)
    """
    num_pixels=3648 #number of effective pixels of CCD

    #External modules loading
    __dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

    #define device handler
    __handle=ctypes.c_long()

    #Set type of argument of functions
    __dev.tlccs_StartScan.argtype=(ctypes.c_long)
    __dev.tlccs_StartScanCont.argtype=(ctypes.c_long)
    __dev.tlccs_SetIntegrationTime.argtypes=(ctypes.c_long,ctypes.c_double)
    __dev.GetWavelengthDataArray.argtype=(ctypes.c_long)
    __dev.GetScanDataArray.argtype=(ctypes.c_long)
    __dev.tlccs_Close.argtype=(ctypes.c_long)
    __dev.OutputErrorMessage.argtypes=(ctypes.c_long,ctypes.c_long)

    #Set type of returned value of functions
    __dev.GetScanDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=num_pixels)
    __dev.GetWavelengthDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=num_pixels)
    
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
        Ccs175m.__dev.tlccs_Init.argtypes=(ctypes.c_char_p,ctypes.c_bool,ctypes.c_bool,ctypes.POINTER(ctypes.c_long))
        err=Ccs175m.__dev.tlccs_Init(self.__name,False,False,ctypes.byref(Ccs175m.__handle))
        if err:
            raise CcsError(status_code=err,session=Ccs175m.__handle)

        #Resister the exit process
        atexit.register(self.close_ccs)

        #get wavelength data
        self.__wavelength=Ccs175m.__dev.GetWavelengthDataArray(Ccs175m.__handle)

        time.sleep(2)
        print('CCS175M is ready.')

    @property
    def wavelength(self):
        return self.__wavelength

    def set_IntegrationTime(self,time=0.01):
        self.iTime=ctypes.c_double(time)
        err=Ccs175m.__dev.tlccs_SetIntegrationTime(Ccs175m.__handle.value,self.iTime)
        if err:
            raise CcsError(status_code=err,session=Ccs175m.__handle,
            msg='If no error message is printed, the value of integration time is probably out of range(1.0e-5 ~ 6.0e+1)')
    
    def start_scan(self):
        err=Ccs175m.__dev.tlccs_StartScanCont(Ccs175m.__handle)
        if err:
            raise CcsError(status_code=err,session=Ccs175m.__handle)
    
    def read_spectra(self,averaging=1):
        data=np.zeros_like(self.wavelength)
        if averaging<1:
            warnings.warn('The value of averaging must always be greater than or equal to 1.')
            averaging=1
        data=Ccs175m.__dev.GetScanDataArray(Ccs175m.__handle)
        print(data,type(data))
        return data
    
    def close_ccs(self):
        err=Ccs175m.__dev.tlccs_Close(Ccs175m.__handle)
        if err:
            raise CcsError(status_code=err,session=Ccs175m.__handle,
            msg='For some reason the equipment could not be disconnected properly')
    
    def output_ErrorMessage(self,status_code:int,session:ctypes.c_long):
        return Ccs175m.__dev.OutputErrorMessage(status_code,session)


        
if __name__=="__main__":
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.ticker import ScalarFormatter

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
    ccs.set_IntegrationTime()
    ccs.start_scan()
    data=ccs.read_spectra()
    wl=ccs.wavelength
    ccs.close_ccs()

    plt.plot(wl,data)
    plt.show()
'''

import matplotlib.pyplot as plt
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
dev.tlccs_SetIntegrationTime.restype=ctypes.c_long
err=dev.tlccs_SetIntegrationTime(handle,integration_time)
if err:
    raise CcsError(status_code=err,session=handle)

#測定開始
err=dev.tlccs_StartScanCont(handle)
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