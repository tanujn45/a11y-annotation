from PyQt5.QtCore import QThread, pyqtSignal


class VideoPlayerThread(QThread):
    pause_signal = pyqtSignal()

    def __init__(self, video_player, end_time_ms):
        super().__init__()
        self.video_player = video_player
        self.end_time_ms = end_time_ms

    def run(self):
        while self.video_player.position() < self.end_time_ms - 40:
            QThread.msleep(10)  # Adjust this value as needed
        self.pause_signal.emit()
