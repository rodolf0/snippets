#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, drange
from scipy.interpolate import interp1d
from datetime import datetime as dt
from datetime import timedelta as tdelta

fechas = [dt(2015, 3,13), dt(2015, 8, 28), dt(2016, 1, 9), dt(2016, 1, 28), dt(2016, 2, 4), dt(2016, 02, 12)]
mcubicos = [42, 67, 160, 166, 169, 171.82]

f = interp1d(date2num(fechas), mcubicos)          # generate interpolation func
x = drange(fechas[0], fechas[-1], tdelta(days=1)) # generate range of points

overlap=True
if overlap:
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax3 = ax1.twinx()
else:
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)


ax1.plot_date(fechas, mcubicos, 'g-')       # plot original data
ax1.set_ylabel('Consumo en m3', color='g')

ax2.plot(x, np.gradient(f(x)), 'b-')
ax2.set_ylabel('m3 / dia', color='b')       # plot rate of change

dt = date2num((fechas[0], fechas[-1]))
dc = (mcubicos[-1] - mcubicos[0]) / (date2num(fechas[-1]) - date2num(fechas[0]))

ax3.plot(dt, (dc, dc), 'r-')
ax3.set_ylabel('m3/dia periodo', color='r') # plot rate of change

fig.autofmt_xdate() # show dates nicely
plt.show()
