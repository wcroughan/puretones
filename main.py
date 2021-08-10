from rtmidi.midiutil import open_midiinput, open_midioutput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout
import sys
import time


class PureTones(QWidget):
    def __init__(self):
        super().__init__()

        self.currentNotes = []
        self.NUM_CHANNELS = 16
        self.MAX_NOTES = self.NUM_CHANNELS

        self.initUI()
        self.initMIDI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("HI!"))
        self.setLayout(layout)

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
        print("on: {}".format(m))

    def noteOff(self, ch, pitch):
        status = NOTE_OFF | ch
        m = [status, pitch, 0]
        self.midiout.send_message(m)
        print("current notes:", self.currentNotes)
        for ni, n in enumerate(self.currentNotes):
            if n[0] == pitch:
                self.currentNotes.pop(ni)
                break
        print("off: {}".format(m))


if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    p = PureTones()
    p.show()
    sys.exit(qapp.exec_())
