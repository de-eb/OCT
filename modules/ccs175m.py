import ctypes
import numpy as np
import matplotlib.pyplot as plt

class CcsError(Exception):
    """Base exception describing for this module.
    See 'class pyvisa.constants.StatusCode(value)[source]' in this site for error details.
    https://pyvisa.readthedocs.io/en/latest/api/constants.html

    Attributes
    ----------
    err: 'int'
        Status codes that VISA driver-level operations can return. 
    """
    def __init__(self, status_code:int, session:int):
        self.err=status_code
        self.inst_handle=session

    def __str__(self):
        dev.tlccs_Close(self.inst_handle)
        return str(pyvisa.constants.StatusCode(self.err))

#dllファイル　ロード
dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M_gsda9.dll')

name='USB0::0x1313::0x8087::M00801544::RAW'
enc_name=name.encode('utf-8')
name=ctypes.create_string_buffer(enc_name)
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


err=dev.tlccs_StartScan(handle)
if err:
    raise CcsError(status_code=err,session=handle)

ccs_num_pixels=3648 #number of effective pixels of CCD
buffer=ctypes.c_double*ccs_num_pixels
buffer2=np.zeros(ccs_num_pixels).astype(np.double)
buffer3=ctypes.c_double() #double buffer3
buffer_p=(ctypes.POINTER(ctypes.c_double)*ccs_num_pixels)()
buffer_c=ctypes.create_string_buffer(ctypes.sizeof((ctypes.c_double)*ccs_num_pixels))
buffer_q=np.ctypeslib.as_ctypes(buffer2)


#getscandataに参照渡しする引数はdouble(*?) data[3648];



#dev.tlccs_GetScanData.argtypes=(ctypes.c_long,buffer_p)
#dev.tlccs_GetScanData.argtypes=[ctypes.c_long,ctypes.POINTER(ctypes.c_double)]
#dev.tlccs_GetScanData(handle,buffer2.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
dev.GetScanDataArray.argtype=(ctypes.c_long)
dev.GetScanDataArray.restype=np.ctypeslib.ndpointer(dtype=np.double,shape=ccs_num_pixels)

data=dev.GetScanDataArray(handle)
plt.plot(data)
plt.show()


#セッション終了

err=dev.tlccs_Close(handle)
if err:
    raise CcsError(status_code=err,session=handle)
