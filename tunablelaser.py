import pyvisa

if __name__ == "__main__":

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    laser = rm.open_resource('GPIB0::14::INSTR')
    laser.read_termination = '\n'
    laser.write_termination = '\n'

    print(laser.query('*IDN?'))
