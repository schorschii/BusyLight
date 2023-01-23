#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import dbus
from dbus.mainloop.glib import DBusGMainLoop

from functools import partial
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
    controller = None
    display = None
    trayIcon = None
    blinker = None
    def __init__(self, configArray, soundcardRecordingDevice, controller, display, trayIcon, *args, **kwargs):
        self.configArray = configArray
        self.soundcardRecordingDevice = soundcardRecordingDevice
        self.controller = controller
        self.display = display
        self.trayIcon = trayIcon
        super(SoundcardMonitor, self).__init__(*args, **kwargs)
    def run(self):
        while True:
            f = open(self.soundcardRecordingDevice, 'r')
            try:
                if('RUNNING' in f.read()): self.controller.busy()
                else: self.controller.idle()
            except Exception: pass
            f.close()
            time.sleep(1)

class LineInputWindow(QtWidgets.QDialog):
    controller = None
    def __init__(self, controller, *args, **kwargs):
        super(LineInputWindow, self).__init__(*args, **kwargs)
        self.controller = controller
        # window layout
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save|QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.txtLine1 = QtWidgets.QLineEdit()
        self.txtLine1.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.txtLine1.setText(self.controller.messageCurrent1)
        self.txtLine1.textChanged.connect(partial(self.inputChanged, self.txtLine1))
        self.layout.addWidget(self.txtLine1)
        self.txtLine2 = QtWidgets.QLineEdit()
        self.txtLine2.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.txtLine2.setText(self.controller.messageCurrent2)
        self.txtLine2.textChanged.connect(partial(self.inputChanged, self.txtLine2))
        self.layout.addWidget(self.txtLine2)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        # window properties
        self.setWindowTitle('Set Idle Text')
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # center screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def closeEvent(self, event):
        event.ignore()
        self.hide()
    def accept(self):
        self.controller.idle(self.txtLine1.text(), self.txtLine2.text())
        self.hide()
    def reject(self):
        self.hide()
    def inputChanged(self, widget, text):
        maxInputLen = 20
        if(len(widget.text()) > maxInputLen):
            text = widget.text()
            text = text[:maxInputLen]
            widget.setText(text)
            widget.setCursorPosition(maxInputLen)

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    parentWidget = None
    controller = None
    def __init__(self, icon, parent):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.parentWidget = parent
        menu = QtWidgets.QMenu(parent)
        setTextAction = menu.addAction('Set Idle Text')
        setTextAction.triggered.connect(self.setText)
        exitAction = menu.addAction('Exit')
        exitAction.triggered.connect(self.exit)
        self.setContextMenu(menu)
        self.activated.connect(self.showMenuOnTrigger)
        self.setToolTip('Sieber Systems BusyLight')
    def showMenuOnTrigger(self, reason):
        if(reason == QtWidgets.QSystemTrayIcon.Trigger):
            self.contextMenu().popup(QtGui.QCursor.pos())
    def setText(self):
        window = LineInputWindow(self.controller, self.parentWidget)
        window.exec_()
    def exit(self):
        QtCore.QCoreApplication.exit()

class BusyLightController():
    configArray = {}
    display = None
    trayIcon = None
    blinker = None
    cleared = False
    messageCurrent1 = ''
    messageCurrent2 = ''
    def __init__(self, configArray, display, trayIcon, *args, **kwargs):
        self.configArray = configArray
        self.display = display
        self.trayIcon = trayIcon
        self.messageCurrent1 = self.configArray['MessageNormal1']
        self.messageCurrent2 = self.configArray['MessageNormal2']
    def processDbusSignal(self, bus, message): # listen for lock screen changes
        if(message.get_member() != 'ActiveChanged'): return
        args = message.get_args_list()
        if(args[0] == True):
            self.messageCurrent1 = self.configArray['MessageAbsent1']
            self.messageCurrent2 = self.configArray['MessageAbsent2']
        elif(args[0] == False):
            self.messageCurrent1 = self.configArray['MessageNormal1']
            self.messageCurrent2 = self.configArray['MessageNormal2']
        self.display.send_text([self.messageCurrent1, self.messageCurrent2])
    def busy(self): # start blinking message
        self.cleared = False
        self.trayIcon.setIcon(QtGui.QIcon(self.configArray['IconBusy']))
        if self.blinker == None:
            self.blinker = MeetingBlink(self.configArray, self.display)
            self.blinker.daemon = True
            self.blinker.start()
    def idle(self, line1=None, line2=None): # clear display
        if(line1 != None):
            self.configArray['MessageNormal1'] = line1
            self.messageCurrent1 = line1
        if(line2 != None):
            self.configArray['MessageNormal2'] = line2
            self.messageCurrent2 = line2
        if not self.cleared or line1 != None or line2 != None:
            self.cleared = True
            self.trayIcon.setIcon(QtGui.QIcon(self.configArray['IconNormal']))
            self.display.send_text([self.messageCurrent1, self.messageCurrent2])
            if self.blinker != None:
                self.blinker.stop()
                self.blinker = None

def main():
    # read configuration values
    configArray = {}
    try:
        configArray = json.load(open(str(Path.home())+'/.config/busylight.json'))
    except Exception as e:
        print(e)
    configArray['DisplaySerialPort'] = configArray.get('DisplaySerialPort', '/dev/ttyUSB0')
    configArray['SoundcardName'] = configArray.get('SoundcardName', None) # None will take the first sound card with input available
    configArray['MessageBusy1'] = configArray.get('MessageBusy1', '   !!! MEETING !!!')
    configArray['MessageBusy2'] = configArray.get('MessageBusy2', 'Please do not disturb.')
    configArray['MessageNormal1'] = configArray.get('MessageNormal1', '')
    configArray['MessageNormal2'] = configArray.get('MessageNormal2', '')
    configArray['MessageAbsent1'] = configArray.get('MessageAbsent1', '')
    configArray['MessageAbsent2'] = configArray.get('MessageAbsent2', '')
    configArray['IconNormal'] = os.path.dirname(os.path.realpath(__file__))+'/normal.svg'
    configArray['IconBusy'] = os.path.dirname(os.path.realpath(__file__))+'/busy.svg'

    # initialize QT tray bar icon
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(configArray['IconNormal']), w)
    trayIcon.show()

    # initialize display driver
    display = pyposdisplay.Driver(config={'customer_display_device_name':configArray['DisplaySerialPort']})
    try:
        for i in range(0, 10):
            display.send_text(['      BusyLight     ', '=='*i])
            time.sleep(0.01)
    except Exception as e:
        # show an error if the serial port is not available
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Unable to connect to line display')
        msg.setText(str(e))
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        retval = msg.exec_()

    # init core busy light controller
    controller = BusyLightController(configArray, display, trayIcon)
    trayIcon.controller = controller

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
    monitor = SoundcardMonitor(configArray, soundcardRecordingDevice, controller, display, trayIcon)
    monitor.daemon = True
    monitor.start()

    # listen for lock screen events
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_match_string("type='signal',interface='org.cinnamon.ScreenSaver'")
    bus.add_message_filter(controller.processDbusSignal)

    # start QT app
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
