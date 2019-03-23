#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 11:16:36 2019

@author: hippo
"""

print(__doc__)

import numpy as np
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QImage

from copy import deepcopy

class Page:
    
    def __init__(self):
        self._backupPoints = list()
        self._bp_id = -1
        self.points = list()
        self.img = QImage()

    def undoClearance(self):
        if len(self._backupPoints) > 0 and self._bp_id > -1:
            self._bp_id -= 1
            self.points = self._backupPoints[self._bp_id]
            
    def redoClearance(self):
        if self._bp_id < len(self._backupPoints)-1:
            self._bp_id += 1
            self.points = self._backupPoints[self._bp_id]

    def addCurPointsToBackup(self):
        dc_points = deepcopy(self.points)
        self._bp_id += 1
        self._backupPoints.insert(self._bp_id, dc_points)

class Pages(QObject):
    
    page_changed_sgnl = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._pages = list()
        self.id = -1
        self.addPage()
        
    def updateCurPageData(self, data):
        page = self.getPage()
        page.points = data.points
        page.img = data.img
        
    @pyqtSlot()
    def addPage(self):
        page = Page()
        newid = self.id + 1
        self._pages.insert(newid, page)        
        self._incrmtId()
        
    @pyqtSlot(int)
    def setPage(self, pid):
        if pid >= 0 and pid < len(self._pages):
            self.id = pid
            self._revalId(signal=True)
        
    @pyqtSlot(int)
    def removePage(self, pid):
        if pid >= 0 and pid < len(self._pages) and len(self._pages) > 1:
            self._pages.remove(pid)
            self._revalId(signal=True)
    
    def getPage(self):
        return self._pages[self.id]
    def getPageId(self):
        return self.id
    
    @pyqtSlot()
    def prevPage(self):
        self._decrmntId()
    @pyqtSlot()
    def nextPage(self):
        if self.id == len(self._pages)-1:
            self.addPage()
        else:
            self._incrmtId()
    
    def _decrmntId(self):
        self.id -= 1
        self._revalId(signal=True)
    def _incrmtId(self):
        self.id += 1
        self._revalId(signal=True)
        
    def _revalId(self, signal=True):
        oldid = self.id
        if self.id < 0 or self.id >= len(self._pages):
            self.id = max(len(self._pages)-1, 0)
        if signal or oldid != self.id:
            self.page_changed_sgnl.emit(self.id)
    
    