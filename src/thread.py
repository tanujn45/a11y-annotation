from PyQt5.QtCore import QThread, pyqtSignal
from src.video_cutter import trim


class Thread(QThread):
    MSG_TRIM_RECORDING = 1
    MSG_EXTRACT_AUDIO = 2

    signal_return_value = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super(Thread, self).__init__()

    def __del__(self):
        self.wait()

    def set_params(self, msg, video_name, start_time, end_time, gesture_name):
        self.msg = msg
        self.video_name = video_name
        self.start_time = start_time
        self.end_time = end_time
        self.gesture_name = gesture_name

    def run(self):
        if self.msg == Thread.MSG_TRIM_RECORDING:
            sub_recording_name = trim(
                self.video_name, self.start_time, self.end_time, self.gesture_name
            )

        self.signal_return_value.emit(1, sub_recording_name)

    def stop(self):
        self.terminate()
