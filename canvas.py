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

from linedrawer import LineDrawer

plt.style.use('dark_background')
np.random.seed(140)

PointsData = namedtuple('PointsData', ['points', 'img'])

def zip_np_arrays(x,y):
	return np.dstack((x, y))[0]

def getOrtho(v):
	"""returns the orthogonal vector of a 2D-vector"""
	return [v[1], -v[0]]

def resizeImage(img, sze, backgr_col):
	tar_sze = QSize(max(img.size().width(), sze.width()),
					max(img.size().height(), sze.height()))
	
	frmt = img.format() if not img.isNull() else QImage.Format_ARGB32
	
	new_img = initImage(tar_sze, backgr_col, frmt)
	if not img.isNull():
		painter = QPainter(new_img)
		
		drawBackgroundToImage(new_img, backgr_col, painter)
		
		painter.drawPixmap(img.rect(), QPixmap.fromImage(img), img.rect())
		painter.end()
		del painter
	return new_img

def drawBackgroundToImage(img, backgr_col, painter=None):
	if img.isNull():
		return
	
	painterValid = painter != None
	if not painterValid:
		painter = QPainter(img)
	else:
		painter.save()
	
	painter.setBrush(QBrush(backgr_col))
	painter.drawRect(img.rect())
	
	if painterValid:
		painter.restore()
	else:
		painter.end()
		del painter

def initImage(sze, backgr_col, frmt=QImage.Format_ARGB32):
	img = QImage(sze.width(), sze.height(), frmt)
	drawBackgroundToImage(img, backgr_col)
	img.fill(0)
	return img

def saveFileDialog(widget):
	options = widgets.QFileDialog.Options()
	options |= widgets.QFileDialog.DontUseNativeDialog
	fileName, _ = widgets.QFileDialog.getSaveFileName(widget,"QFileDialog.getSaveFileName()","","Image Files (*.png);;", options=options)
	return fileName

class Canvas(widgets.QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		
		self.background_color = QColor('#000000')
		self.rubberMode = False
		self.rubberModeStrokeWidthFctr = 20
		self.stroke_width = 1
		self.pen_color = QColor('#00FF00')
		self.col_prev_rct = QRect(0,0,20,20)
								
		self.initImage()
																
		self.points = list()
		self.curDragPoints = list()
		self._initPointsAverager()
		self.reg = list()
				
#		self.setMouseTracking(True)
		
	def setPointsData(self, data):
		self.points = data.points
		self.img = data.img
		self.validateImage()
		self.update()
	def setPoints(self, points):
		self.points = points
		
	def validateImage(self):
		if self.img.isNull():
			self.initImage()
	def getPointsData(self):
		return PointsData(self.points, self.img)
	
	@pyqtSlot()
	def retrieveUpdatedData(self):
		try:
			data = self.dataRetriever()
			self.setPointsData(data)
		except:
			pass
	
	@pyqtSlot()
	def updateData(self):
		try:
			self.dataUpdater(self.getPointsData())
		except:
			pass
	
	def getPoints(self):
		return self.points
	
	def initImage(self):
		self.img = initImage(self.size(), self.background_color)
	
	def drawColorPreview(self):
		self.painter.setBrush(QBrush(self.pen_color))
		self.painter.drawRect(self.col_prev_rct)
		
	def rgba(self):
		return (self.pen_color.red(), 
				self.pen_color.green(), 
				self.pen_color.blue(), 
				self.pen_color.alpha())
	
	@pyqtSlot(int,int,int,int)
	def rgba_changed(self, r,g,b,a):
		self.pen_color = QColor(r,g,b,a)
		self.update()
	
	@pyqtSlot('QString')
	def setPenColor(self, col_hex):
		self.pen_color = QColor(col_hex)
		self.update()
	
	@pyqtSlot()
	def saveImage(self):
		if self.img.isNull():
			return
		img_path = saveFileDialog(self)
		if img_path:
			pixmp = QPixmap.fromImage(self.img)
			pixmp.save(img_path, quality=100)
	
	@pyqtSlot(int)
	def setStrokeWidth(self, sw):
		self.stroke_width = max(sw, 0.25)
		
	def strokeWidth(self):
		return self.stroke_width
	
	def resizeEvent(self, e):
		if not self.img.isNull():
			self.img = resizeImage(self.img, self.size(), self.background_color)
	
	def paintEvent(self, event):
		painter = QPainter(self)
		self.painter = painter
		
		self.paintBackground()
				
		if not self.img.isNull():
			pixmp = QPixmap.fromImage(self.img)
			painter.drawPixmap(pixmp.rect(), pixmp, pixmp.rect())
		
#		for p in self.curDragPoints:
#			col = self.background_color if self.rubberMode else self.pen_color
#			self.drawDispersePoint(p, self.stroke_width, col=col)
		
		self.drawColorPreview()

		painter.end()
		del painter
	
	def createImagePainter(self):
		if self.img.isNull():
			return
		painter = QPainter(self.img)
		self.painter = painter
		
	def deletePainter(self):
		self.painter.end()
		del self.painter
	
	def drawLinesOnImage(self, points):
		if self.img.isNull():
			return
		self.createImagePainter()
		self.drawLines(points)
		self.deletePainter()

	def drawLatestAveragedPontsOnImage(self, averager=None):
		if averager is None:
			averager = self.pntsAvrgr

		# self.pntsAvrgr.getLatestAveragedPoints() - if no new points are available, None is returned!
		latestAvrgdPoints = averager.getLatestAveragedPoints()
		if latestAvrgdPoints is not None:
			self.drawLinesOnImage( latestAvrgdPoints )
		self.update()
	
	@pyqtSlot()
	def clearCanvas(self):
		self._clearPoints()
		self._clearImg()
		self.updateData()
		self.update()
	
	def _clearImg(self):
		if self.img.isNull():
			return
		painter = QPainter(self.img)
		painter.setBrush(QBrush(self.background_color))
		painter.drawRect(self.img.rect())
		painter.end()
		del painter
		
	def _clearPoints(self):
		self.points.clear()
		self.curDragPoints.clear()
		
	def paintBackground(self):
		self.painter.setBrush(QBrush(self.background_color))
		self.painter.drawRect(0,0,10000,10000)
		
	def mouseMoveEvent(self, e):
		self.mouseMovePressed(e)
		
	def mousePressEvent(self, e):
		btns = e.buttons()
		
		if btns == Qt.LeftButton or btns == Qt.RightButton:
			self.rubberMode = btns == Qt.RightButton
			self._initPointsAverager()
			self.curDragPoints = list()
			self.addPoint( (e.x(), e.y()) )	

	def _onAvrgrFinalized(self, averager):
		self.points.append( averager.getPoints() )
		self.updateData()
		self.update()
			
	def mouseReleaseEvent(self, e):				
		#pnts_cnt = len(self.curDragPoints)

		self.pntsAvrgr.finalize()
		#self.points.append( self.pntsAvrgr.getPoints() )
		#self.drawLatestAveragedPontsOnImage()
		
		self.curDragPoints = list()
		
		self.rubberMode = False
		self.update()

	def _initPointsAverager(self):
		pntsAvrgr = PointsAverager()
		pntsAvrgr.rubberMode = self.rubberMode

		def newAvrgPntsAvlbl():
			rmBckup = self.rubberMode
			self.rubberMode = pntsAvrgr.rubberMode
			self._newAveragedPointsAvailable(pntsAvrgr)
			self.rubberMode = rmBckup

		def onFnlzd():
			self._onAvrgrFinalized(pntsAvrgr)

		pntsAvrgr.onNewAvergedPointsAvailable.connect( newAvrgPntsAvlbl )
		pntsAvrgr.onFinalized.connect( onFnlzd )

		self.pntsAvrgr = pntsAvrgr

	def _newAveragedPointsAvailable(self, averager):
		self.drawLatestAveragedPontsOnImage(averager)
		
	def mouseMovePressed(self, e):
		curPnt = (e.x(), e.y())
		self.addPoint(curPnt)
		
	def addPoint(self, p):
		self.curDragPoints.append( p )
		self.pntsAvrgr.addPoint(p)
		#self.drawLatestAveragedPontsOnImage()
		self.update()
		
	def drawLines(self, pnts):
		pen = QPen()
		pen.setWidth(1)
		pen_width = self.stroke_width
		if self.rubberMode:
			pen_width *= self.rubberModeStrokeWidthFctr
		col = self.background_color if self.rubberMode else self.pen_color

		ld = LineDrawer()
		ld.addPoints(pnts)
		ld.drawLines(self.painter, col, pen_width)

