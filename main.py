from rtmidi.midiutil import open_midiinput, open_midioutput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout,  QHBoxLayout, QComboBox
import sys
import time
import numpy as np


class PureTones(QWidget):
    def __init__(self):
        super().__init__()

        self.currentNotes = []
        self.NUM_CHANNELS = 16
        self.MAX_NOTES = self.NUM_CHANNELS
        self.TONE_METHOD_OPTIONS = ["None", "keyroot", "chordroot_et", "chordroot_key"]
        self.tm = None

        self.bendTimeRes = 20  # ms
        self.currentBends = []

        self.initUI()
        self.initMIDI()

    def initUI(self):
        self.mainLayout = QVBoxLayout()

        ls = QHBoxLayout()
        ls.addWidget(QLabel("Method:"))
        cb = QComboBox()
        cb.addItems(self.TONE_METHOD_OPTIONS)
        cb.currentIndexChanged.connect(self.toneMethodChanged)
        ls.addWidget(cb)
        self.mainLayout.addLayout(ls)

        self.tmWidget = QLabel("")
        self.mainLayout.addWidget(self.tmWidget)

        self.setLayout(self.mainLayout)

    def toneMethodChanged(self, idx):
        tmname = self.TONE_METHOD_OPTIONS[idx]

        if tmname == "None":
            self.tm = None
            self.mainLayout.removeWidget(self.tmWidget)
            self.tmWidget = QLabel("")
            self.mainLayout.addWidget(self.tmWidget)
            return
        elif tmname == "keyroot":
            self.tm = TMKeyRoot()
        else:
            print("UNIMPLEMENTED")
            return

        self.mainLayout.removeWidget(self.tmWidget)
        self.tmWidget = self.tm.widget
        self.mainLayout.addWidget(self.tmWidget)

    def initMIDI(self):
        self.midiout, self.outPortName = open_midioutput()
        self.midiin, self.inPortName = open_midiinput()
        self.midiin.set_callback(self)

    def closeEvent(self, event):
        self.midiin.close_port()
        self.midiout.close_port()
        super().closeEvent(event)

    def __call__(self, event, data=None):
        message, cl = event
        if message[0] & 0xF0 == NOTE_ON:
            if len(self.currentNotes) >= self.MAX_NOTES:
                # replace least recently played note
                noteval, ch = self.currentNotes[0]
                self.noteOff(ch, noteval)
                self.noteOn(ch, message[1], message[2])
            else:
                for ch in range(self.NUM_CHANNELS):
                    if any([v[1] == ch for v in self.currentNotes]):
                        continue
                    self.noteOn(ch, message[1], message[2])
                    break
        elif message[0] & 0xF0 == NOTE_OFF:
            for n in self.currentNotes:
                if n[0] == message[1]:
                    self.noteOff(n[1], n[0])
                    break
        else:
            print(event, data)
            self.midiout.send_message(message)

    def noteOn(self, ch, pitch, vel):
        status = NOTE_ON | ch
        m = [status, pitch, vel]
        self.midiout.send_message(m)
        self.currentNotes.append((pitch, ch))
        self.currentBends.append(0)
        print("on: {}".format(m))

        self.recalculateBends()

    def noteOff(self, ch, pitch):
        status = NOTE_OFF | ch
        m = [status, pitch, 0]
        self.midiout.send_message(m)
        print("current notes:", self.currentNotes)
        for ni, n in enumerate(self.currentNotes):
            if n[0] == pitch:
                self.currentNotes.pop(ni)
                self.currentBends.pop(ni)
                break
        print("off: {}".format(m))

        self.recalculateBends()

    def recalculateBends(self):
        if self.tm is not None:
            self.bendEndPoints = self.tm.calculateBends([n[0] for n in self.currentNotes])
        else:
            self.bendEndPoints = [0] * len(self.currentNotes)
        self.bendFrames = np.zeros(
            (len(self.currentNotes), np.ceil(self.bendTime / self.bendTimeRes)))
        bendT = np.arange(np.shape(self.bendFrames)[1])
        for ni in range(len(self.bendEndPoints)):
            self.bendFrames[ni, :] = np.interp(
                bendT, [0, bendT[-1]], [self.currentBends[ni], self.bendEndPoints[ni]])
        self.bendi = 0
        self.bendTimer.start(self.bendTimeRes)

    def bendFunc(self):
        for ni, n in enumerate(self.currentNotes):
            ch = n[1]
            b = self.bendFrames[ni, self.bendi]
            self.pb(ch, b)
            self.currentBends[ni] = b

        self.bendi += 1
        if self.bendi >= np.shape(self.bendFrames)[1]:
            self.bendTimer.stop()

    def pb(self, channel, val):
        print(channel, val)


class ToneMethod:
    def __init__(self, bendRange=(2.0, 2.0)):
        self.widget = QWidget()
        self.bendRange = bendRange

    def calculateBends(self, notes):
        return [0] * len(notes)


class TMKeyRoot(ToneMethod):
    def __init__(self):
        super().__init__()

        self.rootNote = 0
        self.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.scale = 0
        self.SCALE_NAMES = ["Equal Temperament", "Just Intonation"]

        # self.JUST_INTONATION_BENDS = [0, 104, 4, ]

    def initUI(self):
        pass

    def calculateBends(self, notes):
        scname = self.SCALE_NAMES[self.scale]

        if scname == "Equal Temperament":
            return [0] * len(notes)
        elif scname == "Just Intonation":
            for n in notes:
                pass
        else:
            print("UNKNOWN SCALE TYPE")
            return [0] * len(notes)


if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    p = PureTones()
    p.show()
    sys.exit(qapp.exec_())
