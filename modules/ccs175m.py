import ctypes
import pyvisa
import numpy as np

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
dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

#分光器とのセッション確立、セッション番号(アドレス？)の取得
rm=pyvisa.ResourceManager()
inst=rm.open_resource('USB0::0x1313::0x8087::M00801544::RAW')
inst_handle=inst.session

#露光時間設定？
integration_time=ctypes.c_double(0.1)
err=dev.tlccs_SetIntegrationTime(inst_handle,integration_time)
if err:
    raise CcsError(status_code=err,session=inst_handle)


err=dev.tlccs_StartScan(inst_handle)
if err:
    raise CcsError(status_code=err,session=inst_handle)



buffer=(ctypes.c_double*3648)(0)
buffer_p=ctypes.pointer(buffer)
buffer2=np.zeros(3648)

#getscandataに参照渡しする引数はdouble(*?) data[3648];

data=ctypes.c_int64()

dev.tlccs_GetScanData.argtypes=(ctypes.c_int,ctypes.c_double*3648)
err=dev.tlccs_GetScanData(inst_handle)

#<error集>
#err=dev.tlccs_GetScanData(inst_handle,buffer2.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
#例外が発生しました: ArgumentError
#argument 2: <class 'TypeError'>: expected c_double_Array_3648 instance instead of LP_c_double

#err=dev.tlccs_GetScanData(inst_handle,ctypes.POINTER(buffer))
#例外が発生しました: TypeError
#unhashable type

#err=dev.tlccs_GetScanData(inst_handle,buffer)
#例外が発生しました: OSError
#exception: access violation reading 0x0000EA18

#err=dev.tlccs_GetScanData(inst_handle,ctypes.byref(buffer))
#例外が発生しました: ArgumentError
#argument 2: <class 'TypeError'>: expected c_double_Array_3648 instance instead of pointer to c_double_Array_364

print(buffer)


#セッション終了
err=tlccs_Close(inst_handle)
if err:
    raise CcsError(status_code=err,session=inst_handle)
