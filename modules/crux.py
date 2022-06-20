import serial

ser=serial.Serial(
    port='COM4'
)

def decoder(command,param):
    result='\2'+command
    for i in range(len(param)):
        result=result+str(param[i])
        if i+1 != len(param):
            result=result+'/'
    result=result+'\r\n'
    print(result)
    return result.encode('ascii')

move=decoder('APS',[1,0,1000000,0])

ser.write(move)
result=ser.readline()
print(result)