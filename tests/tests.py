import cv2
import numpy as np

import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLabel
from PyQt5.QtGui import QBrush, QPen, QColor, QImage, QPixmap


#create 3 separate BGRA images as our "layers"
w = 500
h = 500
layer1 = np.zeros((h, w, 4), dtype=np.uint8)
layer2 = np.zeros((h, w, 4), dtype=np.uint8)
layer3 = np.zeros((h, w, 4), dtype=np.uint8)

layer1[:,:,3] = 255

#draw a red circle on the first "layer",
#a green rectangle on the second "layer",
#a blue line on the third "layer"
red_color = (0, 0, 255, 255)
green_color = (0, 255, 0, 255)
blue_color = (255, 0, 0, 255)
cv2.circle(layer1, (255, 255), 100, red_color, 5)
cv2.rectangle(layer2, (175, 175), (335, 335), green_color, 5)
cv2.line(layer3, (100, 10), (450, 200), blue_color, 5)

# draw polygon:
pts = np.array([[50,50],[50, 200],[200, 200],[200,50]], np.int32)
pts = pts.reshape((-1,1,2))
print('polygon points: ', pts)
cv2.polylines(layer3,[pts],False,color=(0,255,0, 255), thickness=10)

res = layer1[:] #copy the first layer into the resulting image

#copy only the pixels we were drawing on from the 2nd and 3rd layers
#(if you don't do this, the black background will also be copied)
cnd = layer2[:, :, 3] > 0
res[cnd] = layer2[cnd]
cnd = layer3[:, :, 3] > 0
res[cnd] = layer3[cnd]

blurSze = (3,3)
res = cv2.GaussianBlur(res, blurSze, 0)
res = cv2.GaussianBlur(res, blurSze, 0)
res = cv2.GaussianBlur(res, blurSze, 0)

def genQImage(cvImg):
	height, width, channels = cvImg.shape

	bytesPerLine = channels * width
	imgformat = QImage.Format_RGBA8888 if channels == 4 else Format_RGB888
	qImg = QImage(cvImg, width, height, bytesPerLine, imgformat).rgbSwapped()	
	return qImg

qImg = genQImage(res)

cv2.imwrite("out.png", res)
qImg.save("out2.png")


