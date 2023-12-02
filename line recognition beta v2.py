import cv2, time
import numpy as np
from djitellopy import Tello
import pygame

tello = Tello()
tello.connect()
print(tello.get_battery())
tello.streamon()
tello.takeoff()
tello.move_down(60)
hsvVals = [0,0,131,179,40,255]
sensors = 3
threshold = 0.2
width, height = 480, 360
senstivity = 3  # if number is high less sensitive
weights = [-25, -15, 0, 15, 25]
fSpeed = 15
curve = 0

def thresholding(img):
    hsv= cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([hsvVals[0], hsvVals[1], hsvVals[2]])
    upper = np.array([hsvVals[3], hsvVals[4], hsvVals[5]])
    mask = cv2.inRange(hsv, lower, upper)
    return mask

def getContours(imgThres, img):
    cx = 0
    contours, hieracrhy = cv2.findContours(imgThres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        biggest = max(contours, key=cv2.contourArea)
        x,y,w,h = cv2.boundingRect(biggest)
        cx = x + w // 2
        cy = y + h // 2
        ccx = 240
        ccy = 180
        cv2.drawContours(img, biggest,-1, (255,0,255), 7)
        cv2.circle(img, (cx,cy), 10, (0,255,0), cv2.FILLED)
        cv2.circle(img, (ccx, ccy), 10, (210, 140, 0), cv2.FILLED)
    return cx

def getSensorOutput(imgThres, sensors):
    imgs = np.hsplit(imgThres, sensors)
    totalPixels = (img.shape[1] // sensors) * img.shape[0]
    senOut = []

    for x, im in enumerate(imgs):
        pixelCount = cv2.countNonZero(im)
        if pixelCount > threshold * totalPixels:
            senOut.append(1)
        else:
            senOut.append(0)
        cv2.imshow(str(x), im)
    print(senOut)
    return senOut


def sendCommands(senOut, cx):
    global curve

    lr = (cx - width // 2) // senstivity
    lr = int(np.clip(lr, -10, 10))
    if 2 > lr > -2: lr = 0


    if senOut == [1, 0, 0]: curve = weights[0]
    elif senOut == [1, 1, 0]: curve = weights[1]
    elif senOut == [0, 1, 0]: curve = weights[2]
    elif senOut == [0, 1, 1]: curve = weights[3]
    elif senOut == [0, 0, 1]: curve = weights[4]
    elif senOut == [0, 0, 0]: curve = weights[2]
    elif senOut == [1, 1, 1]: curve = weights[2]
    elif senOut == [1, 0, 1]: curve = weights[2]
    tello.send_rc_control(lr, fSpeed, 0, curve)

while True:
    img = tello.get_frame_read().frame
    img = cv2.resize(img, (width, height))
    img = cv2.flip(img, 0)
    imgThres = thresholding(img)
    cx = getContours(imgThres, img)
    senOut = getSensorOutput(imgThres, sensors)
    sendCommands(senOut, cx)
    cv2.imshow("Output", img)
    cv2.imshow("Path", imgThres)
    cv2.waitKey(1)