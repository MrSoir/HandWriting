#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 21:45:34 2019

@author: hippo
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import norm
from scipy.stats import t as students_t
from scipy.stats import norminvgauss as NIG
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor
import random

from cubic_splines import fit_cubic_spline, cubic_spline

class PointsRegression:
    def __init__(self, points):
        self.points = np.array(points)
        self.project_points()
        self.regress()
        
    def project_points(self):
        self.points_proj = list()
        pnts = self.points
        
        x_diff = pnts[1:, 0] - pnts[:-1, 0]
        x_acc = np.add.accumulate( np.abs(x_diff) )
        x_acc += pnts[0,0]
        x_proj = np.insert(x_acc, 0, pnts[0,0], axis=0)
        
        self.points_proj = zip_np_arrays(x_proj, pnts[:,1])
#        print('points_proj: ', len(self.points_proj))
#        print('points:      ', len(self.points))
        
    def regress(self):
        pnts = self.points_proj
        coeffs, knots = fit_cubic_spline(pnts[:,0], pnts[:,1])
        self.coeffs = coeffs
        self.knots = knots
        
    def genPoints(self, step=5):
        xs_proj = self.points_proj[:,0]
        xmin, xmax = xs_proj[0], xs_proj[-1]
        cnt = int((xmax - xmin) / step)
        xs = np.linspace(xmin, xmax, cnt)

        y_reg = cubic_spline(xs, self.knots, self.coeffs)
        return self.unprojectPoints(xs, y_reg)
#        return zip_np_arrays(xs, y_reg) 

    def unprojectPoints(self, xs, ys):
        pnts_org = self.points
#        pnts_proj = self.points_proj
        
        x_diff_org = pnts_org[1:, 0] - pnts_org[:-1, 0]
        x_acc_org  = np.add.accumulate( x_diff_org ) + pnts_org[0,0]
        x_acc_proj = np.add.accumulate( np.abs(x_diff_org) ) + pnts_org[0,0]
        
        points_unproj = zip_np_arrays(xs,ys)
#        printArr('pnts_org', pnts_org)
#        printArr('x_diff_org', x_diff_org)
#        printArr('points_unproj', points_unproj)
        
        i = 0
        a = 0
        for x_proj,y in zip(xs, ys):
            print()
            for j, x_ac in enumerate(x_acc_proj[i:], start=i):
#                print('j: ', j, '   x_ac: ', x_ac)
                if x_proj < x_ac:
                    break
                if x_proj > x_ac:
                    i = j
#            print('i: ', i)
#            print('x_acc_org[i]:  ', x_acc_org[i])
#            print('x_acc_proj[i]: ', x_acc_proj[i])
#            print('x: ', x_proj)
            vorz = 1 if x_diff_org[i] > 0 else -1
            x_unproj = x_acc_org[i] + (x_proj - x_acc_proj[i]) * vorz
            points_unproj[a,0] = x_unproj
            a += 1
        
#        print()
#        offs = 10
#        printArr('x_acc_org', x_acc_org)
#        printArr('x_acc_proj', x_acc_proj)
#        printArr('points_unproj', points_unproj)
#        print()
        return points_unproj