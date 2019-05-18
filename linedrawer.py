#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 14 07:51:11 2019

@author: hippo
"""

import numpy as np
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor
import random
import math
from linesmoother import smoothImage
import cv2

def QColToArray(col):
	return [col.red(), col.green(), col.blue(), col.alpha()]
	
def arrToUint8Arr(arr):
	return np.array([np.uint8(x) for x in arr])

def toIntArr( arr):
	return [int(x) for x in arr]

class LineDrawer:
	def __init__(self, points=None):
		self.points = None if points is None else self._toNpArray(points)
	
	def reset(self):
		self.points = np.array([])

	def _toNpArray(self, pnts):
		return None if pnts is None else np.array(list(map(np.array, pnts)), dtype=int)
	
	def addPoints(self, newPoints):
		newPoints = self._toNpArray(newPoints)
		print('newPoints: ', newPoints)
		print('points: ', self.points)
		self.points = newPoints# if self.points is None else np.concatenate( (self.points, newPoints), axis=0)

	def _createTransparentImage(self):
		self.line_img = np.zeros((self.imgHeight, self.imgWidth, 4), dtype=np.uint8)
		#self.line_img[:,:,:] = self.col
		#self.line_img[:,:,3] = 0

	def drawLines(self, imgWidth, imgHeight, strokeWidth, col):
		self.strokeWidth = strokeWidth

		if type(col) == QColor:
			qcolarr = QColToArray(col)
			col = arrToUint8Arr(qcolarr)

		self.col = np.array(col, dtype=np.uint8)

		if len(self.col) == 3:
			self.col = np.append(col, 255)

		self.col = toIntArr(self.col)

		self.imgWidth = imgWidth
		self.imgHeight = imgHeight
		self._createTransparentImage()

		#self._drawLines_hlpr()
		self._drawLines_hlpr2()

		#for i in range(1, len(self.points)):
		#	p0 = self.points[i - 1]
		#	p1 = self.points[i]
		#	self._drawLine_hlpr(p0, p1)

		#sclFctr = 2
		#if self.strokeWidth - sclFctr > 2:
		#	self._drawLines_hlpr(self.smoothdImg, self.strokeWidth - sclFctr)

		#return self.line_img
		self.smoothdImg = smoothImage(self.line_img)
		return self.smoothdImg

	def getOrtho(self, p0, p1):
		dirvec = p1 - p0
		ortho = np.array([dirvec[1], -dirvec[0]])
		lngth = np.linalg.norm(ortho)
		ortho = ortho / lngth if lngth != 0 else ortho
		orthoHalfStrokeWidth = ortho * self.strokeWidth * 0.5
		return (ortho, orthoHalfStrokeWidth)

	def initLinePoints(self):
		p0, p1 = self.points[:2]
		_, orthoHalfStrokeWidth = self.getOrtho(p0, p1)
		self.A = p0 + orthoHalfStrokeWidth
		self.B = p0 - orthoHalfStrokeWidth
		self.lastA = self.A
		self.lastB = self.B

	def norm(self, vec):
		lngth = np.linalg.norm(vec)
		return vec / lngth if lngth != 0 else vec

	def _drawLines_hlpr2(self):
		self.initLinePoints()

		for p0, p1, p2 in zip(self.points[:-2], self.points[1:-1], self.points[2:]):
			#self.drawLineOfPoints(p0, p1)
			self.drawLine_hlpr2(p0, p1)

	def drawLine_hlpr2(self, p0, p1, p2=None):
		if p2 == None:
			lastA, lastB = self.lastA, self.lastB
			_, orthoHalfStrokeWidth = self.getOrtho(p0, p1)
			A, B = (p1 + orthoHalfStrokeWidth, p1 - orthoHalfStrokeWidth)
			self.drawPolygonRect_hlpr([lastA, lastB, B, A, lastA])
		else:
			ortho0, _ = self.getOrtho(p1, p0)
			ortho1, _ = self.getOrtho(p1, p2)
			avrgOrtho = (ortho0 + ortho1) * 0.5
			avrgOrtho = ortho0
			avrgOrthoHalf = avrgOrtho * 0.5
			A, B = (p1 + avrgOrthoHalf, p1 - avrgOrthoHalf)
			self.drawPolygonRect_hlpr([lastA, lastB, B, A, lastA])
			self.lastAvrgOrtho = avrgOrtho
		self.lastA, self.lastB = A, B
		
	def drawPolygonRect_hlpr(self, rectPnts):
		pts = np.array(rectPnts, np.int32)
		pts = pts.reshape((-1,1,2))
		cv2.fillPoly(self.line_img, [pts], color=self.col)
		
	
	def _drawLines_hlpr(self, img=None, strokeWidth=None):
		if img is None:
			img = self.line_img
		if strokeWidth is None:
			strokeWidth = self.strokeWidth

		strokeWidth = max(int(strokeWidth), 1)
		
		polylinepnts = [self.points.reshape((-1,1,2))]
		cv2.polylines(img, polylinepnts, isClosed=False, color=toIntArr(self.col), thickness=strokeWidth)

	def _drawLine_hlpr(self, p0, p1):
		if self.line_img is None:
			self._createTransparentImage()

		cv2.line(self.line_img, (p0[0], p0[1]), (p1[0], p1[1]), toIntArr(self.col), self.strokeWidth)

	def drawPoint(self, p, diameter, col, alpha=1.0, id=0):
		cv2.circle(self.line_img, p, int(diameter), (0,255,0, alpha*255), -1)#self.col)

	def toIntTuple(self, xs):
		try:
			return tuple(map(int, xs))
		except:
			return None
	
	def drawLineOfPoints(self, p0, p1):
		x0, y0 = p0
		x1, y1 = p1
		
		step = self.strokeWidth * 0.5
		v0 = np.array([x0,y0])
		v1 = np.array([x1,y1])
		diff = v1 - v0
		lngth = np.linalg.norm(v1 - v0)
		steps = lngth / step if step != 0 else 3
		d = diff / steps
		for i in range(0, int(steps)+1):
			p = v0 + i*d
			intp = self.toIntTuple(p)
			if intp != None:
				self.drawPoint(intp, diameter=self.strokeWidth, col=self.col)
