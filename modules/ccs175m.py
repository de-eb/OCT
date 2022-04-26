import ctypes
import pyvisa

class CcsError(Exception):
    """Base exception describing for this module.
    See 'class pyvisa.constants.StatusCode(value)[source]' in this site for error details.
    https://pyvisa.readthedocs.io/en/latest/api/constants.html

    Attributes
    ----------
    err: 'int'
        Status codes that VISA driver-level operations can return. 
    """
    def __init__(self, status_code:int):
        self.err=status_code

    def __str__(self):
        return str(pyvisa.constants.StatusCode(self.err))



#dllファイル　ロード
dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

#分光器とのセッション確立、セッション番号(アドレス？)の取得
rm=pyvisa.ResourceManager()
inst=rm.open_resource('USB0::0x1313::0x8087::M00801544::RAW')
inst_handle=inst.session



integration_time=ctypes.c_double(2.0e-3)
print(integration_time)
err=dev.tlccs_SetIntegrationTime(inst_handle,integration_time)
got_time=ctypes.c_double()
err=dev.tlccs_GetIntegrationTime(inst_handle,ctypes.byref(got_time))
print(err,got_time)
if True:
    raise CcsError(status_code=-1073807338)