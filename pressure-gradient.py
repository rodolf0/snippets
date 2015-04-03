#!/usr/bin/env python2

import math


def semi_newton_root(f, x0, dx=0.001, epsilon=1.0e-10, max_iter=1000):
  """
  Get the root for function f using x0 as initial point

                         dx
  X_n+1 = X_n - --------------------- * f(X_n)
                 f(X_n + dx) - f(X_n)

  f         is a function object that takes a single real value
  x0        is the initial point for the estimation of f's root
  dx        is an infinitesimal value to estimate f's first derivate
  epsilon   is the allowed error for the root
  max_iter  is the maximum number of iterations before failing
  """

  for i in xrange(max_iter):
    f0, f1 = f(x0), f(x0 + dx)
    d = f0 * dx / (f1 - f0)
    if abs(d) < epsilon:
      break
    x0 -= d
  return x0



def turbulent_friction_factor(Re, D, e):
  """
  Compute the friction factor for turbulent or transition flow regimes

  1/sqrt(f) = -2 log10(e/3.7D + 2.51/Re/sqrt(f))

  Re        is the Reynolds number
  D         is the diameter of the pipeline
  e         is the roughness height

  NOTE: this function has a postive image only, so root finding can fail
  """
  friction_func = lambda f: -1.0/math.sqrt(f) - \
                    2.0 * math.log(e/(3.7*D) + 2.51/(Re * math.sqrt(f)), 10)
  return semi_newton_root(friction_func, 64.0/Re)



def fluid_velocity(Q, D):
  """
  Calculate the velocity of the fluid in a pipeline given it's flow

  v = Q/A   (where A = pi*D^2/4)

  Q         is the flow
  D         is the diameter of the pipeline
  """
  return 4.0 * Q / math.pi / D / D



def pipeline_pressure_drop(p0, l, d, v, a, D, u, e, g=9.8, dx=0.001):
  """
  Compute the presure drop at the end of a pipeline according to

  dP/dx = -d v dv/dx - d g sin(a) - f d v^2 / 2D

  p0        is the pressure at the start of the pipeline (in N/m2 or Pa)
  l         is the length of the pipeline (in m)
  d         is the density of the fluid (in kg/m3)
  v         is the initial velocity of the fluid (in m/s)
  a         is the angle of the pipeline (in rad)
  D         is the diameter of the pipeline (in m)
  u         is the dynamic viscosity of the fluid (in Pa.s == 1000cP)
  e         is the roughness height (in m)
  g         is the earth's gravity (in m/s2)
  dx        is the length of the step for the simulation
  """

  # get the Reynolds number
  Re = d * v * D / u
  # compute the friction factor
  if Re < 2300:
    f = 64.0 / Re
  else:
    f = turbulent_friction_factor(Re, D, e)
  # since flow is constant and the diameter of the section too we assume:
  dv_dx = 0.0
  dp_dx = lambda x, P: -d * v * dv_dx \
                       -d * g * math.sin(a) \
                       -d * f * v*v / 2.0 / D
  x, p = 0.0, p0
  i = 0
  while x < l:
    # runge-kutta's method: no better than euler because dp_dx constant for x,P
    k1 = dx * dp_dx(x, p)
    k2 = dx * dp_dx(x + 0.5*dx, p + 0.5*k1)
    k3 = dx * dp_dx(x + 0.5*dx, p + 0.5*k2)
    k4 = dx * dp_dx(x + dx, p + k3)

    p += (k1 + 2.0*k2 + 2.0*k3 + k4)/6.0
    i+=1
    if i % 100000 == 0:
      print("%fm: %fPa" % (x, p))
    x += dx

  return p



def test():
  p1 = \
  pipeline_pressure_drop(101325.0, # initial pressure in Pa (1 atm)
                         1000.0,   # pipe length in m
                         800.0,    # density in kg/m3
                         fluid_velocity(8000.0/86400.0, 0.2), # in m/s
                         -8.0 * math.pi / 180.0,    # in radians
                         0.2,      # pipe diameter in m
                         0.1,      # 0.1 Pa.s (eq to 100cP)
                         0.0002)   # roughness in m
  p2 = \
  pipeline_pressure_drop(p1,       # initial pressure: the previous pipe output
                         1000.0,   # pipe length in m
                         800.0,    # density in kg/m3
                         fluid_velocity(8000.0/86400.0, 0.1), # in m/s
                         -8.0 * math.pi / 180.0,    # in radians
                         0.1,      # pipe diameter in m
                         0.1,      # 0.1 Pa.s (eq to 100cP)
                         0.0002)   # roughness in m
  print(p2)
