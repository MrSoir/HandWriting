#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 14 08:08:58 2019

@author: hippo
"""

import numpy as np
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor, QImage, QPixmap
import random
import math
import cv2

def smoothImage(img):
	"""
	using gaussian blur to perform line smoothing
	"""
	imgCpy = img[:]
	alphachnl = np.array(imgCpy[:,:,3])
	
	smoothSteps = 2
	kernelSizeFctr = 5
	kernelSize = (kernelSizeFctr,kernelSizeFctr)

	for i in range(smoothSteps):
		alphachnl = cv2.blur(alphachnl, kernelSize)#cv2.GaussianBlur(alphachnl, kernelSize, 0)
	
	imgCpy[:,:,3] = alphachnl

	return imgCpy
