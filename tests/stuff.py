from pylab import *
import numpy as np


# rng = np.random.default_rng()
N = 100000
vals = 1+np.round( np.random.f(3, 2, N)).astype(np.int)

bins = 20
values = arange(bins)
n = zeros(bins)
for val in vals:
    if val <= bins-1 and val >=0:
        n[int(val)] +=1

# print(vals)
print(n/N*100)


plot(values, n, '--o')
show()
