import cv2
import numpy as np

import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor, QImage, QPixmap

class LineDrawer:
	def __init__(self, points):
		self.pnts = np.array([np.array(p) for p in points])
	
	def getOrtho(self, p0, p1):
		dirvec = p1 - p0
		ortho = np.array([dirvec[1], -dirvec[0]])
		ortho = ortho / np.linalg.norm(ortho)
		orthoHalfStrokeWidth = ortho * self.strokeWidth * 0.5
		return (ortho, orthoHalfStrokeWidth)

	def initLinePoints(self):
		p0, p1 = self.pnts[:2]
		_, orthoHalfStrokeWidth = self.getOrtho(p0, p1)
		self.A = p0 + orthoHalfStrokeWidth
		self.B = p0 - orthoHalfStrokeWidth
		self.lastA = self.A
		self.lastB = self.B

	def drawLines(self, cvImg, col, strokeWidth):
		self.cvImg = cvImg
		self.strokeWidth = strokeWidth
		self.col = col

		self.initLinePoints()

		cntr = 0
		for p0, p1, p2 in zip(self.pnts[:-2], self.pnts[1:-1], self.pnts[2:]):
			self.drawLine_hlpr(p0, p1, p2)

		self.drawLine_hlpr( *self.pnts[-2:] )


	def drawLine_hlpr(self, p0, p1, p2=None):
		if p2 is None:
			lastA, lastB = self.lastA, self.lastB
			ortho, _ = self.getOrtho(p0, p1)
			orthoHlf = ortho * 0.5 * self.strokeWidth
			A, B = (p1 + orthoHlf, p1 - orthoHlf)
			self.drawPolygonRect_hlpr([lastA, lastB, B, A, lastA])
		else:
			lastA, lastB = self.lastA, self.lastB
			ortho0, _ = self.getOrtho(p0, p1)
			ortho1, _ = self.getOrtho(p1, p2)
			orthoAvrg = (ortho0 + ortho1) * 0.5
			orthoAvrgHlf = orthoAvrg * 0.5 * self.strokeWidth
			A, B = (p1 + orthoAvrgHlf, p1 - orthoAvrgHlf)
			self.drawPolygonRect_hlpr([lastA, lastB, B, A, lastA])
		self.lastA, self.lastB = A, B
		
	def drawPolygonRect_hlpr(self, rectPnts):
		pts = np.array(rectPnts, np.int32)
		pts = pts.reshape((-1,1,2))
		cv2.fillPoly(self.cvImg, [pts], color=self.col)

def mergeImgs(bckgrnd, overlay):
	mrgdImg =  bckgrnd[:]
	colpxls = overlay[:,:,3] > 0
	bckgrnd[colpxls] = overlay[colpxls]
	return mrgdImg

def _composeImageColors(baseimg, overlay):
	mrgd = cv2.addWeighted(baseimg, 1.0, overlay, 1.0, 0)
	return mrgd

def mergeImages(baseimg, overlayimg):
	return _composeImageColors(baseimg, overlayimg).reshape( baseimg.shape )
	colvals = overlayimg[:,:,3] > 0
	return _composeImageColors(baseimg[colvals], overlayimg[colvals]).reshape( baseimg.shape )


#create 3 separate BGRA images as our "layers"
w = 1000
h = 500
cvImg   = np.zeros((h, w, 4), dtype=np.uint8)
lineImg = np.zeros((h, w, 4), dtype=np.uint8)

tp = cvImg[:,:,3] == 0
cvImg[ tp ] = [0,0,0, 255]

strokeWidth = 8

cv2.circle(cvImg, (255, 255), 100, (0,255,0, 255), strokeWidth)

with open('points', 'rb') as fis:
	linePnts = np.load(fis)#[[10,50],[50, 200],[200, 200],[250,180]]
	linePnts[:,0] -= np.min(linePnts)+10

#linePnts = np.array([[10,50],[50, 200],[200, 200],[250,180]])


lneDrwr = LineDrawer(linePnts)
lneDrwr.drawLines(lineImg, (255,0,255, 255), strokeWidth)

res = lineImg[:] #copy the first layer into the resulting image

blurSze = (5,5)
for i in range(4):
	res = cv2.GaussianBlur(res, blurSze, 0)
	#res = cv2.blur(res, blurSze)

#merge vals:
mrgdImg = mergeImages(cvImg, res)

#lneDrwr.drawLines(res, (255,0,255, 255), 4)


cv2.imwrite("out.png", mrgdImg)


