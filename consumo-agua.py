#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, drange
from scipy.interpolate import interp1d
from datetime import datetime as dt
from datetime import timedelta as tdelta

agua = {
    dt(2015, 3,13)  : 42,
    dt(2015, 8, 28) : 67,
    dt(2016, 1, 9)  : 160,
    dt(2016, 1, 28) : 166,
    dt(2016, 2, 4)  : 169,
    dt(2016, 2, 12) : 171.82,
    dt(2016, 3, 24) : 186.77,
    dt(2016, 8, 25) : 236.02,
}

gas = {
    dt(2015, 3, 11) : 11687.03,
    dt(2016, 1, 9)  : 12292.41,
    dt(2016, 2, 6)  : 12398.31,
    dt(2016, 3, 24) : 12573.40,
    dt(2016, 8, 25) : 12782.96,
}

elec = {
    dt(2016, 1, 9)  : 42889.7,
    dt(2016, 2, 6)  : 43126.8,
    dt(2016, 3, 24) : 43505.7,
    dt(2016, 8, 25) : 44223.3,
}


fig, (xagua, xgas, xelec) = plt.subplots(3, sharex=True)

def build(ax1, servicio, unit):
    fechas, consumos = zip(*sorted(servicio.items()))

    f = interp1d(date2num(fechas), consumos)          # generate interpolation func
    x = drange(fechas[0], fechas[-1], tdelta(days=1)) # generate range of points

    ax1.plot_date(fechas, consumos, 'g-')       # plot original data
    ax1.set_ylabel('Consumo en ' + unit, color='g')

    ax2 = ax1.twinx()
    ax2.plot(x, np.gradient(f(x)), 'b-')
    ax2.set_ylabel(unit + ' / dia', color='b')       # plot rate of change

    dt = date2num((fechas[0], fechas[-1]))
    dc = (consumos[-1] - consumos[0]) / (date2num(fechas[-1]) - date2num(fechas[0]))

    ax3 = ax1.twinx()
    ax3.plot(dt, (dc, dc), 'r-')
    ax3.set_ylabel(unit + '/dia periodo', color='r') # plot rate of change

build(xagua, agua, "m3")
build(xgas, gas, "m3")
build(xelec, elec, "kwh")

fig.autofmt_xdate() # show dates nicely
plt.show()
