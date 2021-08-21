import numpy as np
import matplotlib.pyplot as plt
import math

bu=650
bs=100
x=np.arange(400,1000,1)
broad=(1/math.sqrt(2*np.pi*bs))*np.exp(-0.5*((x-bu)/bs)**2)
ru=633
rs=20
red=(1/math.sqrt(2*np.pi*rs))*np.exp(-0.5*((x-ru)/rs)**2)
print(np.amax(broad),np.amax(red))

plt.plot(x,broad*(np.amax(red)/np.amax(broad)))
plt.plot(x,red)
plt.ylabel('light intensity[a.u.]',fontsize=18)
plt.xlabel('wave length[nm]',fontsize=18)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.show()