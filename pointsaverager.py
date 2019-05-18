#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 21:44:36 2019

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
import math

from cubic_splines import fit_cubic_spline, cubic_spline

class PointsAverager:
    def __init__(self, points):
        self.points = np.array(list(map(np.array, points)))
        self.average_range = 5
        self.average()
        
    def average(self):
        rng = min(self.average_range, len(self.points))
        pnts = [np.array(self.points[rng-i:-i if -i < 0 else len(self.points)]) for i in range(rng)]
        pns_avrg = np.array(pnts[0])
        for p in pnts[1:]:
            pns_avrg += p
        pns_avrg = pns_avrg / rng
        for i in range(2):
            pns_avrg = np.insert(pns_avrg, i, self.points[i], axis=0)
        pns_avrg = np.concatenate( (pns_avrg, [self.points[-1]]), axis=0)
        self.avrgd = pns_avrg
        
    
    @staticmethod
    def genSmoothPoints(points):
        smoothdPoints = []
        points = np.array(list(map(np.array, points)))
        for i in range(2, len(points)):
            p0, p1, p2 = points[i-2: i+1]
            m0 = (p0 + p1) * 0.5
            m1 = (p1 + p2) * 0.5
            
            lngth = lambda p0, p1: math.sqrt( (p0[0]-p1[1])**2 + (p0[1]-p1[1])**2 )
            dt = lngth(m0, m1)
            stps = dt / 2#min(max(dt / 2, 32), 128)
            ts = np.linspace(0, 1, stps)
            quadBezierPnts = PointsAverager.quadBezier(m0, p1, m1, ts)
            smoothdPoints.extend( quadBezierPnts )
        return np.array(smoothdPoints)
                
    @staticmethod
    def quadBezier(p0, p1, p2, t):
        
        Bx = (1-t)**2 * p0[0] + 2 * (1-t) * t * p1[0] + t**2 * p2[0]
        By = (1-t)**2 * p0[1] + 2 * (1-t) * t * p1[1] + t**2 * p2[1]
        return np.dstack( (Bx, By) )[0]

    def getPoints(self):
        return self.avrgd
