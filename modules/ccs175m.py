import ctypes
import numpy as np
import warnings
import atexit
import time

class CcsError(Exception):
    """ Base exception class for this modules.
    Outputs a message to the TERMINAL instead of an exception message
     because of unfixable garbled characters.

    Attributes
    ----------
    err : `int`, required
        Status codes that VISA driver-level operations can return. 
    session : `int`,required
        An instrument handle which is used in call functions.
    msg : `str`
        Message to be output.(For when outputting non-supported message)
    """
    __status_code=ctypes.c_long()
    __err=ctypes.c_long()
    def __init__(self,status_code:ctypes.c_long,session:ctypes.c_long,msg="See terminal for details."):  
        if status_code and session:
            CcsError.__status_code=ctypes.c_long(status_code)
            CcsError.__handle=ctypes.c_long(session)
            Ccs175m.output_ErrorMessage(self,status_code=CcsError.__status_code, session=CcsError.__handle)
            self.__msg=msg
        else:
            self.__msg = '\033[31m' + msg + '\033[0m'
    def __str__(self):
        return self.__msg

class Ccs175m():
    """Class to control compact spectrometer(CCS175/M)
    """
    #External modules loading
    __dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

    num_pixels=3648 #number of effective pixels of CCD

    #define device handler and status code
    __handle=ctypes.c_long()
    __err=ctypes.c_long()

    #Set type of argument of functions
    __dev.tlccs_Init.argtypes=(ctypes.c_char_p,ctypes.c_bool,ctypes.c_bool,ctypes.POINTER(ctypes.c_long))
    __dev.tlccs_StartScan.argtype=(ctypes.c_long)
    __dev.tlccs_StartScanCont.argtype=(ctypes.c_long)
    __dev.tlccs_SetIntegrationTime.argtypes=(ctypes.c_long,ctypes.c_double)
    __dev.GetWavelengthDataArray.argtype=(ctypes.c_long)
    __dev.GetScanDataArray.argtype=(ctypes.c_long)
    __dev.tlccs_Close.argtype=(ctypes.c_long)
    __dev.OutputErrorMessage.argtypes=(ctypes.c_long,ctypes.c_long)

    #Set type of returned value of functions
    __dev.tlccs_Init.restype=(ctypes.c_long)
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
        Ccs175m.__err=Ccs175m.__dev.tlccs_Init(self.__name,False,False,ctypes.byref(Ccs175m.__handle))
        if Ccs175m.__err:
            raise CcsError(status_code=Ccs175m.__err,session=Ccs175m.__handle,msg='CCS175M not found.')

        #Resister the exit process
        atexit.register(self.close_ccs)

        #get wavelength data
        self.__wavelength=Ccs175m.__dev.GetWavelengthDataArray(Ccs175m.__handle)
        print('CCS175M is ready.')

    @property
    def wavelength(self):
        """ Wavelength [nm] axis corresponding to the measurement data.
        """
        return self.__wavelength

    def set_IntegrationTime(self,time=1.0e-3):
        """This function set the optical integration time in seconds.

        Parameters
        ----------
        time : `double`
            The optical integration time [sec].
            Minimum value : 1.0e-5, Maximum value : 6.0e+1

        Raise
        ---------
        CcsError : 
            When an invlid parameter is set. 
        """
        self.iTime=ctypes.c_double(time)
        Ccs175m.__err=Ccs175m.__dev.tlccs_SetIntegrationTime(Ccs175m.__handle.value,self.iTime)
        if Ccs175m.__err:
            raise CcsError(status_code=Ccs175m.__err,session=Ccs175m.__handle)
    
    def start_scan(self):
        """This function starts measurement continuously.
        Any other function except 'read_spectra' function will stop scanning.

        Raise
        --------
        CcsError :
            When measurement could not be started for some reason.
        """
        Ccs175m.__err=Ccs175m.__dev.tlccs_StartScanCont(Ccs175m.__handle)
        if Ccs175m.__err:
            raise CcsError(status_code=Ccs175m.__err,session=Ccs175m.__handle)
    
    def read_spectra(self,averaging=1):
        """This function reads out spectra.
        Be sure to call 'start_scan' function before this function.

        Return
        ---------
        `1d-ndarray`
            Spectra sampled evenly in the wavelength space.
        """
        data=np.zeros_like(self.wavelength)
        if averaging<1:
            warnings.warn('The value of averaging must always be greater than or equal to 1.')
            averaging=1
        for i in range(averaging):
            data2=Ccs175m.__dev.GetScanDataArray(Ccs175m.__handle)
            if np.amax(data2)>=1:
                raise CcsError(status_code=None, session=None,msg="CcsError:Measured data are saturated.")
            data+=data2  
        return data/averaging
    
    def close_ccs(self):
        """ Release the instrument and device driver
        and terminate the connection.
        
        Raise
        -------
        CcsError :
            When the module is not controlled correctly.
        """
        Ccs175m.__err=Ccs175m.__dev.tlccs_Close(Ccs175m.__handle)
        if Ccs175m.__err:
            raise CcsError(status_code=Ccs175m.__err, session=Ccs175m.__handle)

    def output_ErrorMessage(self,status_code:ctypes.c_long,session:ctypes.c_long):
        """This function translates the error return value from VXIplug&play 
        instrument driver function to a user-readable string.

        Parameters
        ----------
        status_code : `ctypes.c_long` 
            Error return value from VXIplug&play instrument driver.
        
        session : `ctypes.c_long`
            Instrument handle of ccs.

        """
        return Ccs175m.__dev.OutputErrorMessage(session,status_code)


if __name__=="__main__":
    import matplotlib.pyplot as plt
    import pandas as pd
    import matplotlib.ticker as ticker

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
    data=np.zeros_like(ccs.wavelength)
    key=None
    err=False
    
    def on_key(event):
        global key
        key=event.key

    #Graph initialization
    fig = plt.figure(figsize=(10, 10), dpi=80, tight_layout=True)
    fig.canvas.mpl_connect('key_press_event', on_key)  # Key event
    ax = fig.add_subplot(111, title='Spectrometer output', xlabel='Wavelength [nm]', ylabel='Intensity [-]')
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.get_yaxis().set_major_locator(ticker.MaxNLocator(integer=True))
    ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    graph, = ax.plot(ccs.wavelength, data)

    while key!='escape':
        try:data=ccs.read_spectra()
        except CcsError as e:
            err=True
            print(e,end="\r")
        else:
            if err:
                print("                            ", end="\r")
                err=False
        graph.set_data(ccs.wavelength,data)
        ax.set_ylim((0,np.amax(data)*1.2))
        ax.set_xlim((770,910))
        key=None
        plt.pause(0.0001)