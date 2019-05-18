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

from collections import namedtuple

class PointDrawer:
	def __init__(self, painter):
		self.painter = painter

	def drawDispersePoint(self, p, diam, col, alpha=None, it=0):
		if alpha is None:
			alpha = col[3] / 255

		red_diam = diam * 1.2
		red_alpha = alpha * 0.8
		if  it < 10:
			self.drawDispersePoint(p, red_diam, col, red_alpha, it+1)
		
		self._drawPoint(p, diam, col, alpha)

	def _drawPoint(self, p, diameter, col, alpha=1):
		x = p[0] - diameter * 0.5
		y = p[1] - diameter * 0.5
		
		q_col = QColor(*col)
		q_col.setAlpha(alpha * 255)
		q_pen = QPen()
		q_pen.setColor(q_col)
		
		brush = QBrush(q_col)
		
		self.painter.setBrush(brush)
		self.painter.setPen(q_pen)
		
		self.painter.drawEllipse(QRectF(float(x), float(y), float(diameter), float(diameter)))
			
