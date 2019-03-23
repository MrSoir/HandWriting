#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 20:15:55 2019

@author: hippo
"""

import matplotlib.pyplot as plt
import numpy as np
from random import random
from scipy import optimize
from collections.abc import Iterable

"""
dieses script kann direkt so gestartet werden -> zeigt im ende eine chart an, das das regressionsergebnis darstellt
"""

# ERROR can be varied to increase the effect of the error terms
ERROR = 0.5

def ref_func(x, error=False):
    """src-function for regression -> error=True will add error terms to randomize data"""
    A = 2
    sigma = 0.1
    omega = 0.1 * 2 * np.pi
    y = A * np.exp(-sigma * x) * np.sin(omega * x)
    e = error * (np.random.rand(*x.shape) * ERROR - ERROR * 0.5)
    y += e
    return y

def tcb(x, K):
    return (x-K)**3 if x > K else 0

def cubic_spline_hlpr(x, knots, coeffs):
    """cubic splie: continuous 1. & 2. derivative"""
    y = 0
    for i in range(4):
        y += coeffs[i] * x**i
    for i, K in enumerate(knots):
        b = coeffs[i+4]
        y += b * tcb(x, K)
    return y

def cubic_spline(xs, knots, coeffs):
    y = np.ones(*xs.shape)
    for i,x in enumerate(xs):
        y[i] = cubic_spline_hlpr(x, knots, coeffs)
    return y

def init_coefficients(knots):
    return np.ones(len(knots) + 4)

def optimization(coeffs, x, knots, y_train):
    return cubic_spline(x, knots, coeffs) - y_train

def fit_cubic_spline(xs, ys, pnts_per_knot=10, knots=None):
    if not isinstance(knots, Iterable):
        xs_stp1, xs_stp2 = xs[pnts_per_knot::pnts_per_knot][:-1], xs[pnts_per_knot+1::pnts_per_knot][:-1]
        knots = np.array([(x1 + x2) / 2. for x1,x2 in zip(xs_stp1, xs_stp2)])
    print('knots: ', knots)
    
    coeffs = init_coefficients(knots)
    
    ls = optimize.least_squares(optimization, coeffs, args=(xs, knots, ys), max_nfev=10)
    return ls.x, knots
#    reg = cubic_spline(xs, knots, ls.x)
#    return (reg, ls.x, knots)

if __name__ == '__main__':
    x_min, x_max = 0, 30
    K_steps = 15
    knots = np.arange(x_min+1, x_max, step=int((x_max-x_min)/K_steps) )
    
    x = np.linspace(x_min,x_max, 200)
    y  = ref_func(x, error=False)
    y_train = ref_func(x, error=True)
    
    plt.plot(x, y_train, 'y.')
    plt.plot(x, y,       'r', linewidth=2)

    coeffs, knots = fit_cubic_spline(x, y_train)#, knots=knots)
    reg = cubic_spline(x, knots, coeffs)
    plt.plot(x, reg, 'b')
