#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 11:16:36 2019

@author: hippo
"""

print(__doc__)

import numpy as np
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel, QFileDialog
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QImage

from copy import deepcopy

import pickle

def openFileNameDialog(init_file_path=None):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    init_file_path = init_file_path if init_file_path else ""
    fileName, _ = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()", init_file_path, "Hand Written Notes (*.hwn)", options=options)
    return fileName
     
def saveFileDialog(init_file_path=None):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    init_file_path = init_file_path if init_file_path else ""
    fileName, _ = QFileDialog.getSaveFileName(None, "Save File", init_file_path,"Hand Written Notes (*.hwn)", options=options)
    return fileName

def SavePages(pages, filepath):
    try:
        with open(filepath, 'wb') as ofs:
            pickler =  pickle.Pickler(ofs, -1)
            pickleSuccess = pickler.dump( pages )
            print('pickleSuccess: ', pickleSuccess)
            return True
#            pickle.dump(pages, ofs, pickle.HIGHEST_PROTOCOL)
    except:# Exception as e:
#        print(e)
        print('could not save pages!')
        return False
        
def imgToByteArray(img):
    qbyte_array = QByteArray()
    stream = QDataStream(qbyte_array, QIODevice.WriteOnly)
    stream << img
    return qbyte_array
def byteArrayToImg(byteArr):
    stream = QDataStream(byteArr, QIODevice.ReadOnly)
    img = QImage()
    stream >> img
    return img

class PageSave:
    def __init__(self, page):
        self._bckpPnts = page._bckpPnts
        self._backupImgs = page._backupImgs
        self._bp_id = page._bp_id
        self.points = page.points
        self.imgbytes = imgToByteArray(page.img)
        
    def toPage(self):
        page = Page()
        page._bckpPnts = self._bckpPnts
        page._backupImgs = self._backupImgs
        page._bp_id = self._bp_id
        page.points = self.points
        page.img = byteArrayToImg(self.imgbytes)
        return page

class Page(QObject):
    
    page_changed_sgnl = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._bckpPnts = list()
        self._backupImgs = list()
        self._bp_id = -1
        self.points = list()
        self.img = QImage()
            
    @pyqtSlot()
    def undo(self):
        if self._bp_id > 0 and len(self._bckpPnts) > 0 and len(self._bckpPnts) > self._bp_id-1:
            self._bp_id -= 1
            self.points = self._bckpPnts[self._bp_id]
            self.img = byteArrayToImg( self._backupImgs[self._bp_id] )
            self.page_changed_sgnl.emit()
    
    @pyqtSlot()
    def redo(self):
        if self._bp_id+1 < len(self._bckpPnts):
            self._bp_id += 1
            self.points = self._bckpPnts[self._bp_id]
            self.img = byteArrayToImg( self._backupImgs[self._bp_id] )
            self.page_changed_sgnl.emit()

    @pyqtSlot()
    def update(self, data):
        self.backup()
        self.points = data.points
        self.img = data.img

    def backup(self):
        self._bp_id += 1
        self.removeOverriddenBackups(self._bp_id)
        self._backupPoints()
        self._backupImage()
        
    def removeOverriddenBackups(self, id):
        del self._bckpPnts[id:]
        del self._backupImgs[id:]
    
    def _backupPoints(self):
        dc_points = deepcopy(self.points)
        self._bckpPnts.insert(self._bp_id, dc_points)

    def _backupImage(self):
        self._backupImgs.append( imgToByteArray(self.img) )
    
    def clearBackups(self):
        del self._bckpPnts[:]
        del self._backupImgs[:]
        del self.points[:]
        self._bp_id = -1
    

class PagesSave:
    def __init__(self, pages):
        self._pages = list()
        self.id = pages.id
        self._saveFileName = pages._saveFileName
        for p in pages.getPages():
            self._pages.append( PageSave(p) )
    
    def toPages(self):
        pages = Pages(False)
        for p in self._pages:
            pages._pages.append( p.toPage() )
        pages.id = self.id
        pages._saveFileName = pages._saveFileName
        return pages


class Pages(QObject):
    
    page_changed_sgnl = pyqtSignal(int)
    
    def __init__(self, addFirstPage=True):
        super().__init__()
        self._pages = list()
        if addFirstPage:
            self.id = -1
            self.addPage()
        else:
            self.id = 0
        self._saveFileName = ''
        
    def __repr__(self):
        return 'Pages(pages: {0})'.format(len(self._pages))
        
    def save(self, askForFilePath = False):
        if askForFilePath or not self._saveFileName:
            self._saveFileName = saveFileDialog(self._saveFileName)
        if not self._saveFileName:
            print('could not save pages')
            return
        # it will be saved twice:
        #   first saving: save data as is
        #   second saving: if plain data was saved, delete the backup-data and save again.
        # => this way, the data will only be deleted when there is already a copy saved to local disk:
        savedSuccessfully = SavePages(PagesSave(self), self._saveFileName)
        if savedSuccessfully:
            for p in self._pages:
                p.clearBackups()
            savedSuccessfully = SavePages(PagesSave(self), self._saveFileName)
        
    def saveAs(self):
        self.save(True)
        
    def filePath(self):
        return self._saveFileName
    
    def _connectPage(self, page):
        page.page_changed_sgnl.connect(self._pageChanged_slot)
    def _connectPages(self):
        for p in self._pages:
            self._connectPage(p)
    
    @pyqtSlot()
    def undo(self):
        self.getPage().undo()
    @pyqtSlot()
    def redo(self):
        self.getPage().redo()
    
    @classmethod
    def openFile(cls, filepath=None):
        if not filepath:
            filepath = openFileNameDialog()
        if filepath:
            try:
                with open(filepath, 'rb') as ifs:
                    pages_serialized = pickle.load(ifs)
                    pages = pages_serialized.toPages()
                    pages._connectPages()
                    return pages
            except:# Exception as e:
#                print(e)
                print('failed to open/read from file')
        else:
            print('no filepath to open selected')
        
    def updateCurPageData(self, data):
        self.getPage().update(data)
        
    @pyqtSlot()
    def addPage(self):
        page = Page()
        self._connectPage(page)
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
            del self._pages[pid]
#            self._pages.remove(pid)
            self._revalId(signal=True)
    
    def getPages(self):
        return self._pages
    
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
            
    @pyqtSlot()
    def _pageChanged_slot(self):
        self.page_changed_sgnl.emit(self.id)

    