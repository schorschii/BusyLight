import pyposdisplay
import threading, time

class MeetingBlink(threading.Thread):
    stopFlag = False
    def stop(self):
        self.stopFlag = True
    def run(self,*args,**kwargs):
        while not self.stopFlag:
            display.send_text(['   !!! MEETING !!!', 'Bitte nicht stoeren.'])
            time.sleep(0.8)
            display.send_text(['', 'Bitte nicht stoeren.'])
            time.sleep(0.8)


soundcardDevice = '/proc/asound/card1/pcm0c/sub0/status'
display = pyposdisplay.Driver()
blinker = None

while True:
    f = open(soundcardDevice, 'r')
    if('RUNNING' in f.read()):
        # start blinking message
        if blinker == None:
            blinker = MeetingBlink()
            blinker.start()
    else:
        # clear display
        display.send_text(['', ''])
        if blinker != None:
            blinker.stop()
            blinker = None

    f.close()
    time.sleep(1)
