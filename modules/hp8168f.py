import time
import pyvisa


class HP8168F:
    """ Class to control tunable laser source (HP-8168F).
    """
    c = 2.998e8  #  Speed of light in a vacuum [m/sec].
    wl_ref = 1580  # Reference wavelength [nm].
    freq_init = c / (wl_ref*1e-9) * 1e-9 # Initial frequency [GHz]

    def __init__(self, gpib_id: str, pin='8168'):
        """ Initiates and unlocks communication with the device.

        Parameters
        ----------
        gpib_id : `str`, required
            GPIB address of the device.

        pin : `str`, optional
            Four-character PIN to unlock the device. Default is 8168.
        """
        # Initialize GPIB.
        self.__rm = pyvisa.ResourceManager()
        self.__dev = self.__rm.open_resource(gpib_id)
        # Set the delimiter and timeout.
        self.__dev.read_termination = '\n'
        self.__dev.write_termination = '\n'
        self.__dev.timeout = None
        # Identify and unlock the device.
        print(self.__dev.query('*IDN?'))
        self.__dev.write(':LOCK OFF,{}'.format(pin))
        # Set the unit of power to Watt.
        self.__dev.write(':POW:UNIT W')
        # Set the reference wavelength.
        self.__dev.write(':WAVE {}NM'.format(HP8168F.wl_ref))
        self.__dev.write(':WAVE:REF:DISP')
        print("HP-8168F is ready.")
    
    def output(self, power: int):
        """ Output laser.
        
        Parameters
        ----------
        power : `int`, required
            Laser intensity [μW]. It can be set between 10 ~ 3000μW.
        """
        self.__dev.write(':POW {}UW'.format(power))
        self.__dev.write(':OUTP ON')
    
    def set_wavelength(self, wavelength: float):
        """ Set the absolute wavelength of the output.
        
        Parameters
        ----------
        wavelength : `float`, required
            Laser wavelength [nm]. It can be set between 1475.000 ~ 1580.000 nm.
        """
        self.__dev.write(':WAVE {:.3f}NM'.format(wavelength))
    
    def set_frequency(self, frequency: float):
        """ Set the absolute frequency of the output.
        
        Parameters
        ----------
        frequency : `float`, required
            Laser frequency [GHz]. It can be set between 189746.8 ~ 203254.2 GHz.
        """
        self.__dev.write(':WAVE:FREQ {}E9'
            .format(frequency - HP8168F.freq_init))

    def stop(self):
        """ Stop the laser output.
        """
        self.__dev.write(':OUTP OFF')
    
    def read_status(self):
        """ Reads the status of the device.

        Returns
        -------
        `dict` Name and data pairs.

            {
                'output'    : bool, State of laser output.
                'power'     : float, Laser power intensity [μW].
                'wavelength': float, Laser wavelength [nm].
                'frequency' : float, Laser frequency [GHz].
            }
        """
        status = {}
        if self.__dev.query(':OUTP?') == '+1':
            status['output'] = True
        else:
            status['output'] = False
        status['power'] = float(self.__dev.query(':POW?')) * 1e6
        status['wavelength'] = float(self.__dev.query(':WAVE?')) * 1e9
        status['frequency'] = (HP8168F.freq_init 
                               + float(self.__dev.query(':WAVE:FREQ?'))*1e-9)
        return status


if __name__ == "__main__":

    laser = HP8168F(gpib_id='GPIB0::24::INSTR', pin=0000)
    print(laser.read_status())
