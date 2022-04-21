import ctypes

instr=ctypes.c_int()
rscStr=ctypes.c_wchar_p('USB0::0x1313::0x8087::M00801544::RAW')

dev=ctypes.windll.LoadLibrary(r'modules\tools\CCS175M.dll')

#dev.vi_OpenDefaultResourceManager(ctypes.byref(resMgr))
#dev.vi_FindResource(resMgr)
err=dev.tlccs_Init(rscStr,0,0,ctypes.byref(instr))

print(instr,err)