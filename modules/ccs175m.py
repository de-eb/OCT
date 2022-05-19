import ctypes
import numpy as np
import matplotlib.pyplot as plt
import chardet

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
    def __init__(self,status_code:int,session:int):
        self.err=status_code
        self.handle=session
        if session:
            dev.tlccs_Close(self.handle)
        self.msg="See terminal for details."
        dev.OutputErrorMessage(self.handle,self.err)
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
        self.name=ctypes.create_string_buffer(name.encode('utf-8'))
        self.handle=ctypes.c_long()
        Ccs175m.__dev.tlccs_Init.argtypes=(ctypes.c_char_p,ctypes.c_bool,ctypes.c_bool,ctypes.POINTER(ctypes.c_long))
        err=Ccs175m.__dev.tlccs_Init(self.name,False,False,ctypes.byref(self.handle))
        if err:
            raise CcsError(status_code=err,session=handle)

        #get wavelength data
        Ccs175m.__dev.GetWavelengthDataArray.argtype=(ctypes.c_long)
        Ccs175m.__dev.GetWavelengthDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=Ccs175m.num_pixels)
        self.__wavelength=Ccs175m.__dev.GetWavelengthDataArray(handle)

        #Set types of arguments and return value of GetScanDataArray function.
        Ccs175m.__dev.GetScanDataArray.argtypes=(ctypes.c_long)
        Ccs175m.__dev.GetScanDataArray.restypes=np.ctypeslib.ndpointer(dtype=np.double,shape=Ccs175m.num_pixels)
    
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
        err=Ccs175m.__dev.tlccs_SetIntegrationTime(self.handle)
        if err:
            raise CcsError(status_code=err,session=handle)

    def read_spectra(self,averaging=1):
        """This function triggers the CCS to take one single scan 
        and reads out the processed scan data.
        """
        Ccs175m.__dev.tlccs_SrartScanCont(handle)
        data=np.zeros()



    def close(self):
        """This function close an instrument driver session.
        
        Raise
        --------
        CcsError :
            When the module is not controlled correctly.
        """
        err=Ccs175m.__dev.tlccs_Close(self.handle)
        if err:
            raise CcsError(status_code=err,session=handle)
        



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
err=dev.tlccs_StartScan(handle)
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
