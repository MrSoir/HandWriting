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
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor
import random
import threading

from cubic_splines import fit_cubic_spline, cubic_spline

class PointsAverager(QObject):
	onNewAvergedPointsAvailable = pyqtSignal()
	onFinalized = pyqtSignal()

	def __init__(self):
		super().__init__()

		self._alrAvrgdId = 0
		self._alrRequestedAvrgdPntsId = 0
		self._minPointsRng = 2
		self.points = None
		self.avrgd = None
		
		self.average_range = 2

	def finalize(self):
		threading.Thread(target=self._finalize_hlpr).start()
		#self._finalize_hlpr()

	def _finalize_hlpr(self):
		self.average()
		self._finalizePoints()
		self.chckForNewAveragedPointsAndSignal()
		self.onFinalized.emit()

	def _finalizePoints(self):
		finalPoints = self.points[self._alrAvrgdId:]
		for i,p in enumerate(finalPoints):
			pnts = finalPoints[i:]
			avgdPnt = self._compAvrg(pnts)
			self._addPointsToAvrgd( np.array([avgdPnt,]) )

	def addPoint(self, p):
		self.addPoints( np.array([p,]) )		

	def addPoints(self, points):
		threading.Thread(target=self._addPoints_hlpr, args=(points,)).start()
		#self._addPoints_hlpr(points)

	def _addPoints_hlpr(self, points):
		self._addPointsToCurPoints(points)
		self.average()
		self.chckForNewAveragedPointsAndSignal()

	def chckForNewAveragedPointsAndSignal(self):
		if self._newAveragedPointsAvailable():
			self.onNewAvergedPointsAvailable.emit()

	def _addPointsToCurPoints(self, points):
		points = points if points is None else np.array(list(map(np.array, points)))

		if self.points is None:
			self.points = points
			self._initAveragePoints()
		else:
			self.points = np.concatenate( (self.points, points) )
	
	def _initAveragePoints(self):
		if self.points is None:
			return
		rng = self.average_range
		for i in range(rng):
			pntsToAvrg = self.points[:i+1]
			avgdPnt = self._compAvrg(pntsToAvrg)
			self._addPointsToAvrgd( np.array([avgdPnt,]) )

	def average(self):
		if self.points is None:
			return
		
		pntsToAvrg = self.points[self._alrAvrgdId:].copy()
		rng = self.average_range
		
		newAvrgdPnts = np.zeros( pntsToAvrg[:-rng].shape )
		
		for i, p0 in enumerate(pntsToAvrg[:-rng]):
			pnts = pntsToAvrg[i:i+rng]
			avgdPnt = self._compAvrg(pnts)
			newAvrgdPnts[i] = avgdPnt
		
		newAvrgPntsCnt = len(newAvrgdPnts)
		if newAvrgPntsCnt > 0:
			self._addPointsToAvrgd( newAvrgdPnts )
			self._alrAvrgdId += newAvrgPntsCnt

	def _addPointsToAvrgd(self, avgdPnts):
		self.avrgd = avgdPnts if self.avrgd is None else np.concatenate( (self.avrgd, avgdPnts) )

	def _compAvrg(self, pntsToAvrg):
		pntsT = pntsToAvrg.T
		return np.sum(pntsT, axis=1) / len(pntsToAvrg)

	def getPoints(self):
		return self.avrgd

	def _newAveragedPointsAvailable(self):
		curAlrdReqstd = self._alrRequestedAvrgdPntsId
		avrgdCnt = len(self.avrgd)

		return avrgdCnt - curAlrdReqstd - 1 > self._minPointsRng

	def getLatestAveragedPoints(self):
		curAlrdReqstd = self._alrRequestedAvrgdPntsId

		if self._newAveragedPointsAvailable():
			self._alrRequestedAvrgdPntsId = len(self.avrgd) - 1
			return self.avrgd[curAlrdReqstd:]
		else:
			return None

