import pyvisa


class HP8168F:

    class SetTo(Enum):
        MIN = 'MIN'
        DEF = 'DEF'
        MAX = 'MAX'
    
    class PowerUnits(Enum):
        DBM = 'DBM'
        WATT = 'W'

    def __init__(self, gpib_id: str, delimiter='\n'):

        self.__rm = pyvisa.ResourceManager()
        # print(self.__rm.list_resources())
        self.__dev = self.__rm.open_resource(gpib_id)
        self.__dev.read_termination = delimiter
        self.__dev.write_termination = delimiter
        print(self.__dev.query('*IDN?'))
    
    def read_hardware_info(self):
        """ The identication query commands the instrument
            to identify  itself over the interface.
        """
        hardware_info = self.__dev.query('*IDN?')
    
    def lock_device(self, lock: bool, password='8168'):
        """ Switches the device-lock OFF and ON.
        """
        self.__dev.write(
            ':LOCK {},{}'.format('ON' if lock else 'OFF', password))
        is_locked = self.__dev.query(':LOCK?')
        return is_locked
    
    def output(self, output: bool, block: bool):
        """ Switches the laser current OFF and ON.
        """
        self.__dev.write(':OUTP {}'.format('ON' if output else 'OFF'))
        self.__dev.write('::POW:ATT:DARK {}'.format('ON' if block else 'OFF'))
    
    def set_output_mode(self, attenuation: bool):
        """ Selects Power or Attenuation Mode. 
            In Power Mode, you specify the output power.
            In Attenuation Mode, you must specify both the laser output power
            and the attenuation level.
        """
        self.__dev.write(
            ':POW:ATT:AUTO {}'.format('ON' if attenuation else 'OFF'))
        mode = self.__dev.query(':POW:ATT:AUTO?')
        return mode
    
    def set_power_units(self, unit: Enum):
        """ Sets the power units.
        """
        self.__dev.write(':POW:UNIT {}'.format(unit))
    
    def adjust(
        self, power: float, attenuation: float, wavelength: float):
        """ Sets the intensity, wavelength and attenuation of the laser.

        Parameters
        ----------
        power : `float` or `Enum`
            laser power(dBm). Set
        level : `float` or `Enum`
            Level of attenuation(dB). Set from 1.5dB to -47dBm
        wavelength : `float` or `Enum`
            wavelength(nm) of laser. Set from 1450nm to 1590nm
        """
        if isinstance(power, HP8168F.SetTo):
            self.__dev.write(':POW {}'.format(power))
        else:
            self.__dev.write(':POW: {}DBM'.format(power))

        if isinstance(attenuation, HP8168F.SetTo):
            self.__dev.write(':POW:ATT {}'.format(attenuation))
        else:
            self.__dev.write(':POW:ATT {}DB'.format(attenuation))
        
        if isinstance(wavelength, HP8168F.SetTo):
            self.__dev.write(':WAVE {}'.format(wavelength))
        else:
            self.__dev.write(':WAVE {}NM'.format(wavelength))
    
    def read_status(self):
        """
        """
        output = self.__dev.query(':OUTP?')
        blind = self.__dev.query(':POW:ATT:DARK?')
        mode = self.__dev.query(':POW:ATT:AUTO?')
        unit = self.__dev.query(':POW:UNIT?')
        power = self.__dev.query(':POW?')
        attenuation = self.__dev.query(':POW:ATT?')
        wavelength = self.__dev.query(':WAVE?')
        status = {
            'output': output,
            'blind': blind,
            'mode': mode,
            'unit': unit,
            'power': power,
            'attenuation': attenuation,
            'wavelength': wavelength}
        return status


if __name__ == "__main__":

    laser = HP8168F('GPIB0::24::INSTR')
    print(laser.read_hardware_info())
