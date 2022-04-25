import ctypes
import pyvisa

class CcsError(Exception):
    """ Base exception class for this modules.
    
    Attributes
    ----------
    msg : `str`
        Human readable string describing the exception.
    
    """

    def __init__(self, msg: str):
        """Set the error message.
    
        Parameters
        ----------
        msg : `str`
            Human readable string describing the exception.
        
        """
        self.msg =msg
    
    def __str__(self):
        """Return the error message."""
        return self.msg


dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')
#instr=ctypes.c_int()
#rscStr=ctypes.c_wchar_p('USB0::0x1313::0x8087::M00801544::RAW')

rm=pyvisa.ResourceManager()
inst=rm.open_resource('USB0::0x1313::0x8087::M00801544::RAW')

inst_handle=inst.session
print(inst_handle)
integration_time=ctypes.c_double(2.0e-3)
print(integration_time)
err=dev.tlccs_SetIntegrationTime(inst_handle,integration_time)
print(err)



#rscStr='USB0::0x1313::0x8087::M00801544::RAW'
#enc_rscStr=str.encode('utf-8')
#rscStr=ctypes.create_string_buffer(enc_rscStr)
#print(enc_rscStr)

#dev.tlccs_Init.argtypes=(ctypes.c_wchar_p,ctypes.c_bool,ctypes.c_bool,ctypes.c_int64)

#if dev.tlccs_init(rscStr.value,True,True,ctypes.byref(instr)):
#    print(instr)
#    raise CcsError(msg='CCS175m not found')

#err=dev.tlccs_init(rscStr.value,True,True,ctypes.byref(instr))