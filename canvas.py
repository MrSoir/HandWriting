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

plt.style.use('dark_background')
np.random.seed(140)

PointsData = namedtuple('PointsData', ['points', 'img'])

def zip_np_arrays(x,y):
    return np.dstack((x, y))[0]

def getOrtho(v):
    """returns the orthogonal vector of a 2D-vector"""

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
        self.stroke_width = 1
        self.pen_color = QColor('#00FF00')
        self.col_prev_rct = QRect(0,0,20,20)
                                
        self.initImage()
                                                                
        self.points = list()
        self.curDragPoints = list()
        self.reg = list()
                
#        self.setMouseTracking(True)
        
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
        
        for p in self.curDragPoints:
            col = self.background_color if self.rubberMode else self.pen_color
            self.drawDispersePoint(p, self.stroke_width, col=col)
        
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
    
    def drawPointOnImage(self, point):
        if self.img.isNull():
            return
        self.createImagePainter()
        self.drawDispersePoint(point, self.stroke_width * 2)
        self.deletePainter()
    def drawLinesOnImage(self, points):
        if self.img.isNull():
            return
        self.createImagePainter()
        self.drawLines(points)
        self.deletePainter()
    
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
            self.curDragPoints = list()
            self.addPoint( (e.x(), e.y()) )    
            
    def mouseReleaseEvent(self, e):                
        pnts_cnt = len(self.curDragPoints)
        
        if pnts_cnt > 2:
            avg = PointsAverager(self.curDragPoints)
            self.points.append( avg.getPoints() )
#            self.drawLines(avg.getPoints())
            
    #        reg = self.fit_regression( self.curDragPoints )
    #        self.drawRegression( reg )
    #        self.reg.append( reg )
        else:
            self.points.append( self.curDragPoints )
            
        self.curDragPoints = list()
        
        self.drawFinalizedPoints(self.points[-1])
        
        self.rubberMode = False
        
    @pyqtSlot()
    def reRenderAllPointPaths(self):
        self.rubberMode = False
        self._clearImg()
        for pnts in self.points:
            self.drawFinalizedPoints(pnts)
        
    def drawFinalizedPoints(self, pntsToDraw):
        if len(pntsToDraw) > 0:
            pnts_cnt = len(pntsToDraw)
            if pnts_cnt > 1:
                self.drawLinesOnImage( pntsToDraw )
            elif pnts_cnt == 1:
                self.drawPointOnImage( pntsToDraw[0] )
        self.updateData()
        self.update()
        
    def mouseMovePressed(self, e):
        curPnt = (e.x(), e.y())
        self.addPoint(curPnt)
        
    def addPoint(self, p):
        self.curDragPoints.append( p )
        self.update()
            
    def drawPoint(self, p, diameter=2., col=None, alpha=1):
        if not col:
            col = self.pen_color
        
        x = p[0] - diameter * 0.5
        y = p[1] - diameter * 0.5
        
        q_col = col
        q_col.setAlpha(alpha * 255)
        q_pen = QPen()
        q_pen.setColor(q_col)
        
        brush = QBrush(q_col)
        
        self.painter.setBrush(brush)
        self.painter.setPen(q_pen)
        
        self.painter.drawEllipse(QRectF(float(x), float(y), float(diameter), float(diameter)))
    
    def drawDispersePoint(self, p, diameter=2, col=None, alpha=1.0):
        if not col:
            col = self.pen_color
#        if not alpha:
#            alpha = self.pen_color.alpha()
        self.colors = [QColor('#00FF00'), QColor('#FFAA00'), QColor('#FF00FF'), QColor('#00FFFF')]
        self.drawDispersePoint_hlpr(p, diam=diameter, col=col, alpha=alpha)
        
    def drawDispersePoint_hlpr(self, p, diam, col, alpha, it=0):
        red_diam = diam * 1.2
        red_diam = min(red_diam, diam+1)
        red_alpha = alpha * 0.8
        if  it < 10:
            self.drawDispersePoint_hlpr(p, red_diam, col, red_alpha, it+1)
        
        self.drawPoint(p, diam, col, alpha)
        
    def fit_regression(self, points):
        return PointsRegression(points)
    def drawRegression(self, reg):
        pnts = reg.genPoints()
        self.drawLines(pnts)
        
#    def drawDisperseLine(self, p0, p1, stroke_width=None, col=None, alpha=1.0):
#        if not stroke_width:
#            stroke_width = self.stroke_width
#        if not col:
#            col = self.pen_color
#        
#        print('p0: ', p0)
#        print('p1: ', p1)
#        
#        v_diff = np.array(p1 - p0)
#        print('v_diff: ', v_diff)
#        
#        length = np.linalg.norm(v_diff)
#        unit_vec = v_diff / length
#        ortho = getOrtho(unit_vec)
#        print('ortho: ', ortho)
#        print('unit_vec: ', unit_vec)
#        print('length: ', length)
#        
#        self.drawDisperseLine_hlpr(p0, p1, ortho, stroke_width, col, alpha)
#        self.drawDisperseLine_hlpr(p0, p1, ortho, stroke_width, col, alpha, vorz = -1)
#        
#        self.drawLine(p0, p1, stroke_width, col, alpha)
#    
#    def drawDisperseLine_hlpr(self, p0, p1, ortho, stroke_width, col, alpha, offs=0.2, vorz = 1., it=1):
#        offs_diff = (1. + offs * it) * vorz
#        ortho_offs = ortho * offs_diff
#        p0_tar = p0 + ortho_offs
#        p1_tar = p1 + ortho_offs
#        
#        red_alpha = alpha * 0.7
#        red_offs = offs * 1.2
#        
#        if it < 8:
#            self.drawDisperseLine_hlpr(p0, p1, ortho, stroke_width, col, red_alpha, red_offs, vorz, it+1)
#        
#        self.drawLine(p0_tar, p1_tar, stroke_width, col, alpha)
#
#    def drawLine(self, p0, p1, stroke_width=None, col=None, alpha=1.0):
#        if not stroke_width:
#            stroke_width = self.stroke_width
#        if not col:
#            col = self.pen_color
#        lne = widgets.QGraphicsLineItem(p0[0], p0[1], p1[0], p1[1])
#        q_col = col
#        q_col.setAlpha(alpha * 255)
#        q_pen = QPen()
#        q_pen.setWidth(stroke_width)
#        q_pen.setColor(q_col)
##        lne.setBrush(QBrush(q_col))
#        lne.setPen(q_pen)
#        self.scene.addItem(lne)
        
    def drawLines(self, pnts):
        pen = QPen()
        pen.setWidth(1)
        pen_width = self.stroke_width
        col = self.background_color if self.rubberMode else self.pen_color
        
        for (x1,y1), (x2,y2) in zip(pnts[:-1], pnts[1:]):
            """line:"""
#            v0, v1 = (np.array([x1, y1]), np.array([x2, y2]))
#            self.drawDisperseLine(v0, v1)
            """points:"""
            step = pen_width * 0.5
            v1 = np.array([x1,y1])
            v2 = np.array([x2,y2])
            diff = v2 - v1
            lngth = np.linalg.norm(v2 - v1)
            steps = lngth / step if step != 0 else 11
            d = diff / steps
            for i in range(0, int(steps)+1):
                p = v1 + i*d
                self.drawDispersePoint(p, diameter=pen_width, col=col)