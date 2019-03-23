#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 10:16:03 2019
==================================================================
@author: Hippo
Script: Spline Regression of handwritten inputs
==================================================================
test to regress handwriting input-points in R²-space:
    - by transforming the R²-Data onto R³-space
    - using spline regression (scipy) to regress the R³-space
    - convert R³-space back to R²-space
==================================================================
"""

print(__doc__)

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
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QImage

import random

from canvas import Canvas

from cubic_splines import fit_cubic_spline, cubic_spline

from page import Pages, Page

plt.style.use('dark_background')
np.random.seed(140)


#button = QPushButton('Click')
#def on_button_clicked():
#    alert = QMessageBox()
#    alert.setText('You clicked the button!')
#    alert.exec_()
#
#button.clicked.connect(on_button_clicked)
#button.MainWindow()

def genColors(ro, rr, go, gr, bo, br, steps = 20):
    r = np.linspace(max(ro, 0), min(ro+rr, 255), steps-1)
    g = np.linspace(max(go, 0), min(go+gr, 255), steps-1)
    b = np.linspace(max(bo, 0), min(bo+br, 255), steps-1)
    
    colors = [QColor(int(r[i]), int(g[i]), int(b[i])) for i in range(len(r))]

#    for c in colors:
#        print(c.name())
#    print()
    return colors

class MainWindow(QWidget):
    
    rgba_changed_sgnl = pyqtSignal(int, int, int, int)
    stroke_width_changed_sgnl = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        self.pages = Pages()
        self.pages.page_changed_sgnl.connect(self.pageChanged)
        
        self.background_color = QColor('#000000')
        self.foreground_col = QColor('#00FF00')
                                     
#        self.setStyleSheet("QLabel { color : #FFFFFF; }; QPushButton {background-color : #00FF00; color : #FF0000}");
        self.setStyleSheet("""  QLabel { color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AABBAA, stop:1 #AAFFAA); } 
                                QPushButton { background-color : #002200; color : #AAFFAA; }
                                QLineEdit { background-color : #004400; color : #AAFFAA; }
                                
                                QSlider::groove:horizontal {
                                    border: 1px solid #000000;
                                    height: 8px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
                                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005500, stop:1 #008800);
                                    margin: 2px 0;
                                }
                                
                                QSlider::handle:horizontal {
                                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00BB55, stop:1 #00DD88);
                                    border: 1px solid #5c5c5c;
                                    width: 20px;
                                    margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
                                    border-radius: 3px;
                                }
                           """);

        self.initUI()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        self.painter = painter
        
        self.paintBackground()

        painter.end()
        del painter
    
    def paintBackground(self):
        self.painter.setBrush(QBrush(self.background_color))
        self.painter.drawRect(0,0,10000,10000)
        
    def initUI(self):      
        mainLay = widgets.QVBoxLayout()
        self.mainLay = mainLay
        mainLay.setContentsMargins(0,0,0,0)
        mainLay.setSpacing(0)
        
        self.slider_grid = widgets.QGridLayout()
        self.slider_grid.setContentsMargins(10,10,10,10)
        self.slider_grid.setColumnStretch(0,0)
        self.slider_grid.setColumnStretch(1,1)
        self.slider_grid.setColumnStretch(2,1)
        
        self.canvas = Canvas()
        self.rgba_changed_sgnl.connect(self.canvas.rgba_changed)
        self.stroke_width_changed_sgnl.connect(self.canvas.setStrokeWidth)
        self.canvas.setPointsData(self.pages.getPage())
        
        self.clearBtn = widgets.QPushButton('Clear Canvas')
        self.clearBtn.clicked.connect(self.clearCanvas)
        self.undoClearBtn = widgets.QPushButton('Undo')
        self.undoClearBtn.clicked.connect(self.undoClearCanvas)
        self.redoClearBtn = widgets.QPushButton('Redo')
        self.redoClearBtn.clicked.connect(self.redoClearCanvas)
        clearlay = widgets.QHBoxLayout()
        clearlay.setSpacing(20)
        clearlay.addWidget(self.clearBtn)
        clearlay.addWidget(self.undoClearBtn)
        clearlay.addWidget(self.redoClearBtn)
        
        self.saveBtn = widgets.QPushButton('Save')
        self.saveBtn.clicked.connect(self.canvas.saveImage)
        
        mainLay.addWidget(self.canvas)
        mainLay.addLayout(clearlay)
        self.genPageBar()
        self.generateColorPicker()
        self.genColorPickerGrid()
        self.generateMetaSliders()
        mainLay.addWidget(self.saveBtn)
        
        self.setLayout(mainLay)
        
        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle('Hand Writing')
        self.show()
    
    @pyqtSlot()
    def clearCanvas(self):
        self.pages.getPage().addCurPointsToBackup()
        self.canvas.clearCanvas()
    @pyqtSlot()
    def undoClearCanvas(self):
        page = self.pages.getPage()
        page.undoClearance()
        self.canvas.setPoints(page.points)
        self.canvas.reRenderAllPointPaths()
    @pyqtSlot()
    def redoClearCanvas(self):
        page = self.pages.getPage()
        page.redoClearance()
        self.canvas.setPoints(page.points)
        self.canvas.reRenderAllPointPaths()
        
    def genColorPickerGrid(self):
        colgrid = widgets.QGridLayout()
        colgrid.setSpacing(0)
        colgrid.setContentsMargins(0,0,0,0)
        low = 40
        rc = genColors(low, 255, 0, 0, 0, 0)
        gc = genColors(0, 0, low, 255, 0, 0)
        bc = genColors(0, 0, 0, 0, low, 255)
        c1 = genColors(low, 255, 0, 150, 0, 0)
        c2 = genColors(low, 255, 0, 0, 0, 150)
        c3 = genColors(0, 0, 0, 150, low, 255)
        c4 = genColors(0, 255, 0, 255, 0, 255)
        
        for c,rs in enumerate(zip(rc, gc, bc, c1, c2, c3, c4)):
            for r, col in enumerate(rs):
                btn = self.genColorButton(col)
                colgrid.addWidget(btn, r, c)
        
        self.slider_grid.addLayout(colgrid, 0, 2, 5, 1)
    
    def setPenColor(self, col):
        q_col = QColor(col)
        r,g,b,a = q_col.red(), q_col.green(), q_col.blue(), q_col.alpha()
        self.red.setValue( int(r / 255 * (self.red.maximum()-self.red.minimum())) )
        self.grn.setValue( int(g / 255 * (self.grn.maximum()-self.grn.minimum())) )
        self.blu.setValue( int(b / 255 * (self.blu.maximum()-self.blu.minimum())) )
        self.alp.setValue( int(a / 255 * (self.alp.maximum()-self.alp.minimum())) )
#        self.red.value(), self.grn.value(), self.blu.value(), self.alp.value()
#        self.canvas.setPenColor(col)
        
    def genColorButton(self, col):
        btn = widgets.QPushButton()
        btn.setStyleSheet( "QPushButton {" + " background-color : {0}".format(col.name()) + "; } " )
        setPenCol = lambda: self.setPenColor(col.name())
        btn.clicked.connect(setPenCol)
        return btn
    
    def generateMetaSliders(self):
        grid = self.slider_grid
        
        self.stroke_fctr = 10
        
        sw = self.genSlider()#widgets.QSlider(Qt.Horizontal)
        sw.setValue( self.canvas.strokeWidth() * self.stroke_fctr )
        
        sw.setMinimum( int(0.5 * self.stroke_fctr) )
        sw.setMaximum( int(20 * self.stroke_fctr) )
        sw.valueChanged.connect( self.stroke_width_changed )
        
        swlgl = self.genLbl('stroke width: ')
        
        grid.addWidget(swlgl, 4, 0)
        grid.addWidget(sw,    4, 1)#, Qt.AlignLeft)
    
    def generateColorPicker(self):
        grid = self.slider_grid
        
        red = self.genSlider()#widgets.QSlider(Qt.Horizontal)
        grn = self.genSlider()#widgets.QSlider(Qt.Horizontal)
        blu = self.genSlider()#widgets.QSlider(Qt.Horizontal)
        alp = self.genSlider()#widgets.QSlider(Qt.Horizontal)
        
        r,g,b,a = self.canvas.rgba()
        
        red.setValue(int( r * 100. / 255. ))
        grn.setValue(int( g * 100. / 255. ))
        blu.setValue(int( b * 100. / 255. ))
        alp.setValue(int( a * 100. / 255. ))
        
        self.red = red
        self.grn = grn
        self.blu = blu
        self.alp = alp
        
        red.valueChanged.connect(self.rgba_changed)
        grn.valueChanged.connect(self.rgba_changed)
        blu.valueChanged.connect(self.rgba_changed)
        alp.valueChanged.connect(self.rgba_changed)
        
        rlbl = self.genLbl('red:  ')
        glbl = self.genLbl('green:')
        blbl = self.genLbl('blue: ')
        albl = self.genLbl('alpha:')
        
        lay = grid # self.mainLay
        
        lay.addWidget(rlbl, 0, 0)
        lay.addWidget(glbl, 1, 0)
        lay.addWidget(blbl, 2, 0)
        lay.addWidget(albl, 3, 0)
        
        lay.addWidget(red, 0, 1)#, Qt.AlignLeft)
        lay.addWidget(grn, 1, 1)#, Qt.AlignLeft)
        lay.addWidget(blu, 2, 1)#, Qt.AlignLeft)
        lay.addWidget(alp, 3, 1)#, Qt.AlignLeft)
        
        self.mainLay.addLayout(grid)
    
    def genSlider(self):
        sldr = widgets.QSlider(Qt.Horizontal)
        sldr.setMaximumWidth(200)
        sldr.setMinimumWidth(200)
        return sldr
    
    def genLbl(self, txt):
        lbl = widgets.QLabel(txt)
        return lbl
    
    def genPageBar(self):
        prev = widgets.QPushButton('prev')
        nxt  = widgets.QPushButton('next')
        page_lbl = widgets.QLabel('page:')
        page = widgets.QLineEdit() # auf 0 indexiert, linedit aber auf  indexiert
        self.page_le = page
        self.update_page_le()
        
        prev.clicked.connect(self.prevPage)
        nxt.clicked.connect(self.nextPage)
        page.textChanged.connect(self.setPage)
        
        pagelay = widgets.QHBoxLayout()
        pagelay.setSpacing(10)
        pagelay.addWidget(prev)
        pagelay.addWidget(nxt)
        pagelay.addWidget(page_lbl)
        pagelay.addWidget(page)
        
        self.mainLay.addLayout(pagelay)
    
    def update_page_le(self):
        self.page_le.setText( '{0}'.format(self.pages.getPageId()+1) )
    
    @pyqtSlot(int)
    def pageChanged(self, page_id):
        self.update_page_le()
        cur_page = self.pages.getPage()
        self.canvas.setPointsData( cur_page )
    
    def savePageData(self):
        page_data = self.canvas.getPointsData()
        self.pages.updateCurPageData(page_data)
    
    @pyqtSlot()
    def nextPage(self):
        self.savePageData()
        self.pages.nextPage()
    
    @pyqtSlot()
    def prevPage(self):
        self.savePageData()
        self.pages.prevPage()
    
    @pyqtSlot('QString')
    def setPage(self, page_str):
        try:
            page_id = int(page_str) - 1 # auf 0 indexiert, linedit aber auf  indexiert
            if self.pages.getPageId() != page_id:
                self.savePageData()
                self.setPage_hlpr(page_id)
        except:
            pass
    
    def setPage_hlpr(self, page_id):
        self.pages.setPage(page_id)
        
    @pyqtSlot(int)
    def stroke_width_changed(self, val):
        self.stroke_width_changed_sgnl.emit( val / self.stroke_fctr )

    @pyqtSlot()
    def rgba_changed(self):
        r,g,b,a = self.red.value(), self.grn.value(), self.blu.value(), self.alp.value()
        r = int( r * 255. / 100. )
        g = int( g * 255. / 100. )
        b = int( b * 255. / 100. )
        a = int( a * 255. / 100. )
        self.rgba_changed_sgnl.emit(r,g,b,a)
        
if __name__ == '__main__':
    app = widgets.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())