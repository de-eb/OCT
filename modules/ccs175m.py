import pyvisa
import time

rm=pyvisa.ResourceManager()
print(rm.list_resources('?*'))

inst=rm.open_resource('USB0::0x1313::0x8087::M00801544::RAW')
inst.write("*idn?")
out=inst.read()
print(out)