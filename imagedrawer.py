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
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QImage
import random
import math
import cv2

def _composeImageColors(baseimg, overlay):
	return cv2.addWeighted(baseimg, 1.0, overlay, 1.0, 0)

def mergeImages(baseimg, overlayimg):
	return 
	colvals = overlayimg[:,:,3] > 0
	nonTrasnpPxls = overlayimg[colvals]
	baseimg[colvals] = _composeImageColors(baseimg[colvals], overlayimg[colvals])
	return baseimg #np.clip(baseimg, 0, 255)

def genQImage(cvImg):
	height, width, channels = cvImg.shape

	bytesPerLine = channels * width
	imgformat = QImage.Format_RGBA8888 if channels == 4 else Format_RGB888
	qImg = QImage(cvImg.data, width, height, bytesPerLine, imgformat).rgbSwapped()	
	return qImg

