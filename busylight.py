#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from pathlib import Path
import pyposdisplay
import threading, time
import glob
import json
import sys, os

class MeetingBlink(threading.Thread):
    configArray = []
    display = None
    stopFlag = False
    def __init__(self, configArray, display, *args, **kwargs):
        self.configArray = configArray
        self.display = display
        super(MeetingBlink, self).__init__(*args, **kwargs)
    def run(self, *args, **kwargs):
        while True:
            if self.stopFlag: break
            self.display.send_text([self.configArray['MessageBusy1'], self.configArray['MessageBusy2']])
            time.sleep(0.8)
            if self.stopFlag: break
            self.display.send_text(['', self.configArray['MessageBusy2']])
            time.sleep(0.8)
    def stop(self):
        self.stopFlag = True

class SoundcardMonitor(threading.Thread):
    configArray = []
    soundcardRecordingDevice = None
    display = None
    trayIcon = None
    blinker = None
    def __init__(self, configArray, soundcardRecordingDevice, display, trayIcon, *args, **kwargs):
        self.configArray = configArray
        self.soundcardRecordingDevice = soundcardRecordingDevice
        self.display = display
        self.trayIcon = trayIcon
        super(SoundcardMonitor, self).__init__(*args, **kwargs)
    def run(self):
        cleared = False
        while True:
            f = open(self.soundcardRecordingDevice, 'r')
            if('RUNNING' in f.read()):
                # start blinking message
                cleared = False
                self.trayIcon.setIcon(QtGui.QIcon(self.configArray['IconBusy']))
                if self.blinker == None:
                    self.blinker = MeetingBlink(self.configArray, self.display)
                    self.blinker.daemon = True
                    self.blinker.start()
            else:
                # clear display
                if not cleared:
                    cleared = True
                    self.trayIcon.setIcon(QtGui.QIcon(self.configArray['IconNormal']))
                    self.display.send_text([self.configArray['MessageNormal1'], self.configArray['MessageNormal2']])
                    if self.blinker != None:
                        self.blinker.stop()
                        self.blinker = None

            f.close()
            time.sleep(1)

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        exitAction = menu.addAction('Exit')
        self.setContextMenu(menu)
        exitAction.triggered.connect(self.exit)
    def exit(self):
        QtCore.QCoreApplication.exit()

def main():
    # read configuration values
    configArray = {}
    try:
        configArray = json.load(open(str(Path.home())+'/.config/busylight.json'))
    except Exception as e:
        print(e)
    configArray['SoundcardName'] = configArray['SoundcardName'] if 'SoundcardName' in configArray else None # None will take the first sound card with input available
    configArray['MessageBusy1'] = configArray['MessageBusy1'] if 'MessageBusy1' in configArray else '   !!! MEETING !!!'
    configArray['MessageBusy2'] = configArray['MessageBusy2'] if 'MessageBusy2' in configArray else 'Please do not disturb.'
    configArray['MessageNormal1'] = configArray['MessageNormal1'] if 'MessageNormal1' in configArray else ''
    configArray['MessageNormal2'] = configArray['MessageNormal2'] if 'MessageNormal2' in configArray else ''
    configArray['IconNormal'] = os.path.dirname(os.path.realpath(__file__))+'/normal.svg'
    configArray['IconBusy'] = os.path.dirname(os.path.realpath(__file__))+'/busy.svg'

    # initialize display driver
    display = pyposdisplay.Driver()

    # initialize QT tray bar icon
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(configArray['IconNormal']), w)
    trayIcon.show()

    # find desired sound card and start monitoring sound device
    soundcardRecordingDevice = None
    for name in glob.glob('/proc/asound/card*/id'):
        f = open(name, 'r')
        checkSoundcardName = f.read().strip()
        if checkSoundcardName == configArray['SoundcardName'] or configArray['SoundcardName'] == None:
            soundcardDevice = name.rstrip('/id')
            for name2 in glob.glob(soundcardDevice+'/pcm*c/sub0/status'):
                print(f'Monitoring {name2} ({checkSoundcardName}) sound device')
                soundcardRecordingDevice = name2
                break
        if soundcardRecordingDevice != None:
            break
        f.close()
    monitor = SoundcardMonitor(configArray, soundcardRecordingDevice, display, trayIcon)
    monitor.daemon = True
    monitor.start()

    # start QT app
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
