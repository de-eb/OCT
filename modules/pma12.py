from ctypes import *

windll.LoadLibrary('modules\WnPmaUSB.dll')
windll.LoadLibrary('modules\StopMsg.dll')
pma = windll.LoadLibrary('modules\PmaUsbW32.dll')

print(pma.StartDevice())
print(pma.EndDevice())
