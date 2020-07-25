import pyvisa

command = [
    '*IDN?',
    ':LOCK ON|OFF,0000',
    ':OUTP ON|OFF',  # laser output
    ':POW:UNIT DBM|DBMW|W'  # power unit
    ':POW:ATT:AUTO ON|OFF',  # attenuation mode
    ':POW:ATT:DARK ON|OFF',
    ':POW:ATT <val>DB|DEF|MIN|MAX',  # attenuation level[dBm]
    ':POW <val>DB|DEF|MIN|MAX',  # laser output power[dBm]
    ':WAVE <val>',  # wavelength[m]
    ]

if __name__ == "__main__":

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    laser = rm.open_resource('GPIB0::14::INSTR')
    laser.read_termination = '\n'
    laser.write_termination = '\n'

    print(laser.query('*IDN?'))
