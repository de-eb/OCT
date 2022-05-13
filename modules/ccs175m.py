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
dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M_st4.dll')

name='USB0::0x1313::0x8087::M00801544::RAW'
enc_name=name.encode('utf-8')
name=ctypes.create_string_buffer(enc_name)
dev.StringTest(name)
#dev.StringTest.argtypes=[ctypes.c_wchar_p]
#print('name = ',name.value)
#print(dev.StringTest("USB0::0x1313::0x8087::M00801544::RAW"))

'''
dev.tlccs_Init_Simple.argtypes=(ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_long))
dev.tlccs_Init_Simple.restype=ctypes.c_long

handle=ctypes.c_long()
err=dev.tlccs_Init_Simple('USB0::0x1313::0x8087::M00801544::RAW',ctypes.byref(handle))
print(handle)


#分光器とのセッション確立、セッション番号の取得
rm=pyvisa.ResourceManager()
inst=rm.open_resource('USB0::0x1313::0x8087::M00801544::RAW')


#露光時間設定
integration_time=ctypes.c_double(0.1)
err=dev.tlccs_SetIntegrationTime(inst.session,integration_time)
if err:
    raise CcsError(status_code=err,session=inst.session)


err=dev.tlccs_StartScan(inst.session)
if err:
    raise CcsError(status_code=err,session=inst.session)



buffer=ctypes.c_double*3648
buffer3=ctypes.c_double() #double buffer3
buffer_p=ctypes.POINTER(ctypes.c_double*3648)
buffer2=np.zeros(3648)

#getscandataに参照渡しする引数はdouble(*?) data[3648];

data=ctypes.c_int64()
#buffer=dev.GetScanDataArray(inst.session)

#dev.tlccs_GetScanData.argtypes=(ctypes.c_long,buffer_p)
dev.tlccs_GetScanData(inst.session,ctypes.byref(buffer))

#err=dev.tlccs_GetScanData(inst.session,buffer2.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
#dev.GetScanDataArray.restype=(ctypes.c_double)*3648
#dev.tlccs_GetScanData(inst.session)



#セッション終了

err=dev.tlccs_Close(inst.session)
if err:
    raise CcsError(status_code=err,session=inst.session)
'''