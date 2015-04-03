#!/usr/bin/env python2

# Derived from http://sundararajana.blogspot.com/2007/05/motion-detection-using-opencv.html

import cv
from Xlib import X, display

class BallTracker:
  def __init__(self, display):
    self.capture = cv.CaptureFromCAM(0)
    self.frame_size = cv.GetSize(cv.QueryFrame(self.capture))
    self.win = cv.NamedWindow("Ball", 1)
    self.win = cv.NamedWindow("Normal", 1)
    self.win = cv.NamedWindow("Line", 1)
    self.display = display


  def getFrame(self):
    frame = cv.QueryFrame(self.capture)
    #cv.Smooth(frame, frame, cv.CV_GAUSSIAN, 3, 0)
    cv.Flip(frame, frame, 1)
    return frame


  def getThresholdedFrame(self):
    hsv = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 3)
    cv.CvtColor(self.getFrame(), hsv, cv.CV_RGB2HSV)

    thres = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 1)
    thres2 = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 1)

    #cv.InRangeS(hsv, cv.Scalar(55, 80, 40), cv.Scalar(75, 220, 150), thres)
    #cv.InRangeS(hsv, cv.Scalar(235, 80, 40), cv.Scalar(255, 220, 150), thres2)
    cv.InRangeS(hsv, cv.Scalar(55, 100, 40), cv.Scalar(75, 220, 120), thres)
    cv.InRangeS(hsv, cv.Scalar(235, 100, 40), cv.Scalar(255, 220, 120), thres2)
    cv.Or(thres, thres2, thres)

    cv.Smooth(thres, thres, cv.CV_GAUSSIAN, 9, 9)
    return thres


  def run(self):
    x, y, lastx, lasty = -1, -1, -1, -1

    screen = self.display.screen()

    scrible = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 3)
    tmp = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_32F, 1)

    cv.SetZero(scrible)
    cv.SetZero(tmp)

    while True:
      # Display frame to user
      frame = self.getFrame()
      thres = self.getThresholdedFrame()

      seq = cv.FindContours(thres, cv.CreateMemStorage())
      biggest = None
      while seq:
        if cv.ContourArea(seq) > 1600:
          if not biggest or cv.ContourArea(biggest) < cv.ContourArea(seq):
            biggest = seq
        seq = seq.h_next()

      if biggest:
        moments = cv.Moments(biggest)
        area = cv.GetSpatialMoment(moments, 0, 0)
        x = int(cv.GetSpatialMoment(moments, 1, 0) / area)
        y = int(cv.GetSpatialMoment(moments, 0, 1) / area)
        if lastx != -1 and lasty != -1:
          cv.Line(scrible, (lastx, lasty), (x, y), cv.Scalar(10, 10, 200), thickness=3)
          screen.root.warp_pointer(x,y)
          self.display.sync()
        lastx, lasty = x, y
      else:
        lastx, lasty = -1, -1

      cv.Add(frame, scrible, frame)
      cv.ShowImage("Normal", frame)
      cv.ShowImage("Ball", thres)
      cv.ShowImage("Line", scrible)


      # Listen for ESC or ENTER key
      c = cv.WaitKey(7) % 0x100
      if c == 27:
        break
      elif c == 10:
        cv.SetZero(scrible)


  def run2(self):
    x, y, lastx, lasty = 0, 0, 0, 0

    #scrible = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 3)
    #tmp = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_32F, 1)

    #cv.SetZero(scrible)
    #cv.SetZero(tmp)

    while True:
      # Display frame to user
      frame = self.getFrame()
      thres = self.getThresholdedFrame()

      #storage = cv.CreateMat(1, thres.width * thres.height, cv.CV_32FC3)
      #circles = cv.HoughCircles(thres, storage, cv.CV_HOUGH_GRADIENT,
                                #2, thres.height/4, 100, 40, 20, 200)
      #if circles:
        #maxrad = 0
        #maxc = None
        #print circles
        #for c in circles:
          #if c[2] > maxrad:
            #maxc = c

        #if maxc:
          #lastx, lasty = x, y
          #x, y = int(c[0]), int(c[1])
          #cv.Line(scrible, (lastx, lasty), (x, y), cv.Scalar(0, 255, 0))

      #cv.Add(frame, scrible, frame)
      cv.ShowImage("Normal", frame)
      cv.ShowImage("Ball", thres)
      #cv.ShowImage("Line", scrible)


      # Listen for ESC or ENTER key
      c = cv.WaitKey(7) % 0x100
      if c == 27:
        break
      elif c == 10:
        cv.SetZero(scrible)


  def run3(self):
    x, y, lastx, lasty = 0, 0, 0, 0

    scrible = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_8U, 3)
    #tmp = cv.CreateImage(self.frame_size, cv.IPL_DEPTH_32F, 1)

    cv.SetZero(scrible)
    #cv.SetZero(tmp)

    while True:
      # Display frame to user
      frame = self.getFrame()
      thres = self.getThresholdedFrame()

      #storage = cv.CreateMat(1, thres.width * thres.height, cv.CV_32FC3)
      #circles = cv.HoughCircles(thres, storage, cv.CV_HOUGH_GRADIENT,
                                #2, thres.height/4, 100, 40, 20, 200)

      #seq = cv.FindContours(thres, cv.CreateMemStorage())
      #biggest = None
      #while seq:
        #if cv.ContourArea(seq) > 1600:
          #if not biggest or cv.ContourArea(biggest) < cv.ContourArea(seq):
            #biggest = seq
        #seq = seq.h_next()

      #if biggest:
        #lastx, lasty = x, y
        #moments = cv.Moments(biggest)
        #area = cv.GetSpatialMoment(moments, 0, 0)
        #x = int(cv.GetSpatialMoment(moments, 1, 0) / area)
        #y = int(cv.GetSpatialMoment(moments, 0, 1) / area)
        #cv.Line(scrible, (lastx, lasty), (x, y), cv.Scalar(0, 255, 0))


      #if circles:
        #maxrad = 0
        #maxc = None
        #print circles
        #for c in circles:
          #if c[2] > maxrad:
            #maxc = c

        #if maxc:
          #lastx, lasty = x, y
          #x, y = int(c[0]), int(c[1])
          #cv.Line(scrible, (lastx, lasty), (x, y), cv.Scalar(0, 255, 0))

      #cv.Add(frame, scrible, frame)
      cv.ShowImage("Normal", frame)
      cv.ShowImage("Ball", thres)
      #cv.ShowImage("Line", scrible)


      # Listen for ESC or ENTER key
      c = cv.WaitKey(7) % 0x100
      if c == 27:
        break
      elif c == 10:
        cv.SetZero(scrible)

if __name__=="__main__":
  BallTracker(display.Display()).run()
