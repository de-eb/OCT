import serial
import atexit
import warnings

'''
move=decoder('APS',[1,0,10000,0])

ser.write(move)
result=ser.readline()
print(result)

origin=decoder('ORG',[1,5,0])
ser.write(origin)
result=ser.readline()
print(result)
'''

class Crux:
    """Class to control 1-axis auto stage (CRUX)
    """
    def __init__(self,port:str,baudrate=9600):
        self.__port=port
        self.__baudrate=baudrate
    
        try:
            self.__ser=serial.Serial(
                port=self.__port,
                baudrate=self.__baudrate,
            )
        except serial.serialutil.SerialException:
            raise CruxError(msg="CRUX not found.")
        
        atexit.register(self.close)
        self.hw_info=self.read_hw_info()
        if self.hw_info[0]!='C' or self.hw_info[2]!='CRUX':
            print(self.hw_info)
            raise CruxError(msg="*IDN? query failed.\n")
        print("CRUX is ready.")

    def __cmdmaker(self,cmd:str,param=[]):
        command='\2'+cmd
        for i in range(len(param)):
            command=command+str(param[i])
            if i+1 !=len(param):
                command=command+'/'
        command=command+'\r\n'
        return command.encode('ascii')
    
    def __read(self):
        result=self.__ser.readline().decode('utf-8')
        return result.split()

    def read_hw_info(self):
        self.__ser.write(self.__cmdmaker('IDN'))
        return self.__read()
    
    def move_origin(self,axis_num=1,velocity=5,ret_form=0,warn=True):
        self.__ser.write(self.__cmdmaker('ORG',[axis_num,velocity,ret_form]))
        responce=self.__read()
        if responce[0]=='E':
            raise CruxError(msg='An problem has occured. See error code and manual for detauils.\nError Code:'+str(responce))
        elif responce[0]=='W' and warn:
            warnings.warn(str(responce))

    def close(self):
        self.move_origin()
        self.__ser.close()

class CruxError(Exception):
    """Base exception class for this modules.

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
        self.msg = '\033[31m' + msg + '\033[0m'
    
    def __str__(self):
        """Return the error message."""
        return self.msg

if __name__=="__main__":
    stage=Crux('COM4')