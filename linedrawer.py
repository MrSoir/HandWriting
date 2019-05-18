#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 21:42:11 2019

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
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QRect, QRectF, QSize
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QImage
import random

from cubic_splines import fit_cubic_spline, cubic_spline
from pointsaverager import PointsAverager
from pointsregression import PointsRegression

from pointdrawer import PointDrawer

from collections import namedtuple

class LineDrawer:
	def __init__(self, points=None):
		self.pnts = None if points is None else self._toNpArray(points)
		self.pntsId = 0

	def addPoints(self, points):
		if self.pnts is None:
			self.pnts = self._toNpArray(points)
		else:
			self.pnts = np.concatenate((self.pnts, points), axis=0)

	def _toNpArray(self, pnts):
		return None if pnts is None else np.array(list(map(np.array, pnts)))

	def drawLines(self, painter, col, strokeWidth):
		self.pointDrawer = PointDrawer(painter)
		
		if type(col) == QColor:
			col = np.array([col.red(), col.green(), col.blue(), col.alpha()])

		self.col = np.array(col)
		if len(self.col) == 3:
			self.col = np.append(self.col, 1)

		self.strokeWidth = strokeWidth

		self.painter = painter
		
		for p0, p1 in zip(self.pnts[self.pntsId:-1], self.pnts[self.pntsId+1:]):
			self._drawLine(p0, p1)
		self.pntsId = len(self.pnts)
	
	def _drawLine(self, p0, p1):
		x0, y0 = p0
		x1, y1 = p1
		step = self.strokeWidth * 0.5

		strkWdth = self._evalStrokeWidth(p0, p1)

		diff = p1 - p0
		lngth = np.linalg.norm(p1 - p0)
		steps = lngth / step if step != 0 else 10
		d = diff / steps
		for i in range(0, int(steps)+1):
			p = p0 + i*d
			self.pointDrawer.drawDispersePoint(p, strkWdth, self.col)

	def _evalStrokeWidth(self, p0, p1):
		dx = p1 - p0
		lngth = np.linalg.norm(dx)
		mindx = 2
		maxdx = 5
		maxreduc = 0.65
		if lngth <= mindx:
			return self.strokeWidth
		elif lngth >= maxdx:
			return self.strokeWidth * maxreduc
		else:
			def f(x):
				return maxreduc + (1 - maxreduc) * (1 - np.log(x+1))
			def evalpercentage(x, srcmin, srcmax):
				return (x - srcmin) / (srcmax - srcmin)
			tarminx = 0
			tarmaxx = np.exp(1) - 1
			perc = evalpercentage(lngth, mindx, maxdx)
			tarx = 1 - perc
			return self.strokeWidth * (1 - (1 - maxreduc) * perc)


