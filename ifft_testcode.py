
import numpy as np
import matplotlib.pyplot as plt

# 10x10のダミーデータ作成
mat = np.random.rand(10,10)*1e-3

print(type(mat))
# ヒートマップ表示
plt.figure()
plt.imshow(mat,aspect=2)
plt.colorbar()
plt.show()
