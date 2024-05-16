from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import sys
from src.thread import Thread
from src.video_thread import VideoPlayerThread
import pandas as pd
import os
import numpy as np

sys.settrace


class AnnotationWindow(QMainWindow):
    def __init__(self, parent=None):
        super(AnnotationWindow, self).__init__(parent)
        self.setWindowTitle("Annotation tool")
        self.showFullScreen()
        # self.resize(AnnotationWindow.WIN_SIZE[0], AnnotationWindow.WIN_SIZE[1])
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveDVDIcon))

        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.is_finished = True
        self.thread = None

        self.record_start_time = None
        self.record_end_time = None
        self.curr_start_time_ms = 0
        self.curr_end_time_ms = 0
        self.curr_playing = False
        self.video_name = ""
        self.gesture_name = ""
        self.acc_data = None
        self.frequency = 50
        self.final_end_time = 0
        self.data_folder = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
        self.video_player_thread = None

        self.setStyleSheet(
            """
            QWidget {
                font: 15px 'Roboto Mono';
            }

            QPushButton { 
                background-color: black; 
                color: white; 
                padding: 10px 20px;
                border-radius: 5px;
            } 
            
            QMainWindow { 
                background-color: #202124; 
            } 

            QVideoWidget {
                border-radius: 5px;
            }
            
            QLabel { 
                color: white; 
            } 

            QSlider {
                padding: 10px;
            }
            
            QLineEdit { 
                background-color: #2a2b2e; 
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid black;
            } 
            
            QStatusBar { 
                background-color: black; 
            }

            QListWidget {
                background-color: #202124;
                color: white;
            }
            """
        )

        self.widget_video = QVideoWidget()

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.timestampLabel = QLabel("")
        self.statusbar.addPermanentWidget(self.timestampLabel)

        pixmap_play = self.style().standardPixmap(QStyle.SP_MediaPlay)
        painter_play = QPainter(pixmap_play)
        painter_play.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_play.fillRect(pixmap_play.rect(), QColor("white"))
        painter_play.end()
        self.icon_play = QIcon(pixmap_play)

        pixmap_pause = self.style().standardPixmap(QStyle.SP_MediaPause)
        painter_pause = QPainter(pixmap_pause)
        painter_pause.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_pause.fillRect(pixmap_pause.rect(), QColor("white"))
        painter_pause.end()
        self.icon_pause = QIcon(pixmap_pause)

        self.icon_playPause = QIcon(
            "/Users/tanujnamdeo/Desktop/AAC/annotation/pausePlay.png"
        )

        self.button_play = QPushButton()
        self.button_play.setIcon(self.icon_play)
        self.button_play.clicked.connect(self.play_video)

        pixmap_ff = self.style().standardPixmap(QStyle.SP_MediaSkipForward)
        painter_ff = QPainter(pixmap_ff)
        painter_ff.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_ff.fillRect(pixmap_ff.rect(), QColor("white"))
        painter_ff.end()
        icon_ff = QIcon(pixmap_ff)

        self.button_ff = QPushButton()
        self.button_ff.setIcon(icon_ff)
        self.button_ff.clicked.connect(self.arrow_right_event)

        pixmap_bb = self.style().standardPixmap(QStyle.SP_MediaSkipBackward)
        painter_bb = QPainter(pixmap_bb)
        painter_bb.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_bb.fillRect(pixmap_bb.rect(), QColor("white"))
        painter_bb.end()
        icon_bb = QIcon(pixmap_bb)

        self.button_bb = QPushButton()
        self.button_bb.setIcon(icon_bb)
        self.button_bb.clicked.connect(self.arrow_left_event)

        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setTickInterval(100)
        self.video_slider.setRange(0, 0)
        self.video_slider.sliderMoved.connect(self.set_position)
        self.video_duration = 0

        # Action 'Open'
        self.action_open = QAction(QIcon("open.png"), "&Open", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.setStatusTip("Open a video")
        self.action_open.triggered.connect(self.open_video)

        # Menu bar
        self.menu_bar = self.menuBar()
        self.menu_menu = self.menu_bar.addMenu("&Menu")
        self.menu_menu.addAction(self.action_open)

        # Main Widget
        self.widget_window = QWidget(self)
        self.setCentralWidget(self.widget_window)

        # Annotate button (layout_operation)
        self.layout_operation = QHBoxLayout()
        self.layout_operation.setContentsMargins(0, 0, 0, 0)
        self.textbox_register = QLineEdit()
        self.textbox_register.setPlaceholderText("Enter gesture name")
        # add icon and text to QPushButton

        self.button_annotate = QPushButton(" Record")
        self.button_annotate.setIcon(
            self.style().standardIcon(QStyle.SP_DialogSaveButton)
        )
        self.layout_operation.addWidget(self.textbox_register)
        self.layout_operation.addSpacing(10)
        self.layout_operation.addWidget(self.button_annotate)

        # Set start, end and clear button (layout_record)
        self.layout_record = QHBoxLayout()
        self.layout_record.setContentsMargins(0, 0, 0, 0)
        self.button_start = QPushButton("Begin")
        self.button_end = QPushButton("End")
        self.button_clear = QPushButton("Clear")
        self.layout_record.addWidget(self.button_start)
        self.layout_record.addSpacing(2)
        self.layout_record.addWidget(self.button_end)
        self.layout_record.addSpacing(2)
        self.layout_record.addWidget(self.button_clear)
        self.button_start.clicked.connect(self.record_start)
        self.button_end.clicked.connect(self.record_end)
        self.button_annotate.clicked.connect(self.record_trim_recording)
        self.button_clear.clicked.connect(self.record_clear)

        # Play button and slider (layout_widget)
        self.layout_widget = QHBoxLayout()
        self.layout_widget.setContentsMargins(0, 0, 0, 0)
        self.layout_widget.addWidget(self.button_bb)
        self.layout_widget.addWidget(self.button_play)
        self.layout_widget.addWidget(self.button_ff)
        self.layout_widget.addWidget(self.video_slider)

        # Video layout (video_layout_window)
        self.video_layout_window = QVBoxLayout()
        self.video_layout_window.addWidget(self.widget_video)
        self.video_layout_window.addLayout(self.layout_widget)
        self.video_layout_window.addLayout(self.layout_record)
        self.video_layout_window.addLayout(self.layout_operation)

        # Graph and recorded gestures (widget_graph)
        self.widget_graph = pg.plot(title="Accelerometer Data")
        self.plots = [
            self.widget_graph.plot(pen=pg.mkPen(color=("r", "g", "b")[i]))
            for i in range(3)
        ]
        self.widget_graph.setLabel("left", "Acceleration", units="m/s^2")
        self.widget_graph.showGrid(x=True, y=True)
        self.layout_graph_register = QVBoxLayout()

        self.label_gesture_name = QLabel("Gestures")
        self.label_start_time = QLabel("Begin")
        self.label_end_time = QLabel("End")
        self.label_controls_1 = QLabel("")
        self.label_controls_2 = QLabel("")
        self.heading_layout = QHBoxLayout()

        self.label_gesture_name.setContentsMargins(10, 0, 0, 0)
        self.label_start_time.setContentsMargins(20, 0, 0, 0)
        self.label_end_time.setContentsMargins(10, 0, 0, 0)
        self.label_controls_1.setContentsMargins(0, 0, 0, 0)
        self.label_controls_2.setContentsMargins(0, 0, 0, 0)

        self.heading_layout.addWidget(self.label_gesture_name, 3)
        self.heading_layout.addWidget(self.label_start_time, 3)
        self.heading_layout.addWidget(self.label_end_time, 3)
        self.heading_layout.addWidget(self.label_controls_1, 1)
        self.heading_layout.addWidget(self.label_controls_2, 1)
        self.widget_annotations = QListWidget()
        self.layout_graph_register.setContentsMargins(0, 0, 0, 0)
        self.layout_graph_register.addWidget(self.widget_graph)
        self.layout_graph_register.addLayout(self.heading_layout)
        self.layout_graph_register.addWidget(self.widget_annotations)

        # Main layout
        self.layout_window = QHBoxLayout()
        self.layout_window.addLayout(self.video_layout_window, 2)
        self.layout_window.addLayout(self.layout_graph_register, 3)

        # Window layout
        self.widget_window.setLayout(self.layout_window)

        self.video_player.setVideoOutput(self.widget_video)
        self.video_player.setNotifyInterval(100)
        self.video_player.stateChanged.connect(self.media_state_changed)
        self.video_player.positionChanged.connect(self.position_changed)
        self.video_player.durationChanged.connect(self.duration_changed)
        self.video_player.error.connect(self.error_control)

        self.populate_annotations()

    def populate_annotations(self):
        data_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
        master_csv_path = data_path + "master.csv"

        if os.path.exists(master_csv_path):
            df = pd.read_csv(master_csv_path)
            for index, gesture in df.iterrows():
                # Create a QWidget
                item_widget = QWidget()

                # Create a QHBoxLayout
                item_layout = QHBoxLayout(item_widget)

                # Create the labels and buttons
                label_name = QLabel(gesture["Gesture name"])
                label_name.setFixedWidth(200)
                edit_start = QLineEdit(str(gesture["Start time"]))
                edit_end = QLineEdit(str(gesture["End time"]))
                button_play = QPushButton()
                button_play.setIcon(self.icon_playPause)
                button_play.clicked.connect(
                    self.create_play_function(gesture["Filename"], edit_start, edit_end)
                )
                button_save = QPushButton()
                button_save.setIcon(
                    self.style().standardIcon(QStyle.SP_DialogSaveButton)
                )
                button_save.clicked.connect(
                    self.create_save_function(
                        gesture["Filename"],
                        gesture["Gesture name"],
                        edit_start,
                        edit_end,
                    )
                )

                # Add the labels and buttons to the layout
                item_layout.addWidget(label_name, 3)
                item_layout.addWidget(edit_start, 3)
                item_layout.addWidget(edit_end, 3)
                item_layout.addWidget(button_play, 1)
                item_layout.addWidget(button_save, 1)

                # Create a QListWidgetItem
                item = QListWidgetItem(self.widget_annotations)

                # Set the widget of the QListWidgetItem to the QWidget
                item.setSizeHint(item_widget.sizeHint())
                self.widget_annotations.setItemWidget(item, item_widget)

    def create_play_function(self, video_name, start_time, end_time):
        return lambda: self.play_annotated_video(
            video_name, float(start_time.text()), float(end_time.text())
        )

    def play_annotated_video(self, video_name, start_time, end_time):
        if self.curr_playing and self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
            self.curr_playing = False
            self.video_player_thread.terminate()
            return

        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()

        if start_time > end_time:
            self.statusbar.showMessage(
                "Error: The start time should be earlier than the end time."
            )
            return

        if start_time == end_time:
            self.statusbar.showMessage(
                "Error: The duration of the gesture cannot be 0."
            )
            return

        self.statusbar.showMessage("Info: Loading the video '" + video_name + "' ...")
        start_time = round(start_time, 1)
        end_time = round(end_time, 1)
        self.video_name = (
            "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/raw_video/"
            + video_name
            + ".mp4"
        )

        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_name)))

        if not self.check_media_status():
            return

        self.open_csv()
        start_time_ms = int(start_time * 1000)
        end_time_ms = int(end_time * 1000)
        self.curr_start_time_ms = start_time_ms
        self.curr_end_time_ms = end_time_ms
        self.video_player.setPosition(start_time_ms)
        self.statusbar.showMessage("Info: Playing the video '" + video_name + "' ...")
        self.video_player.play()
        self.curr_playing = True

        self.video_player_thread = VideoPlayerThread(self.video_player, end_time_ms)
        self.video_player_thread.pause_signal.connect(self.handle_pause)
        self.video_player_thread.start()

    def handle_pause(self):
        self.video_player.setPosition(self.curr_start_time_ms)
        self.video_player_thread.start()

    def create_save_function(self, filename, gesture_name, edit_start, edit_end):
        # @dev: Need to trim video here too
        master_csv_path = self.data_folder + "master.csv"

        def save_function():
            if edit_start.text() == "" or edit_end.text() == "":
                self.statusBar().showMessage(
                    "Error: Please input the start and end times."
                )
                return

            if float(edit_start.text()) > float(edit_end.text()):
                self.statusBar().showMessage(
                    "Error: The start time should be earlier than the end time."
                )
                return

            if float(edit_start.text()) == float(edit_end.text()):
                self.statusBar().showMessage(
                    "Error: The duration of the gesture cannot be 0."
                )
                return

            new_start_time = float(edit_start.text())
            new_end_time = float(edit_end.text())

            df = pd.read_csv(master_csv_path)

            master_start_time = df.loc[
                (df["Filename"] == filename) & (df["Gesture name"] == gesture_name),
                "Start time",
            ].values[0]
            master_end_time = df.loc[
                (df["Filename"] == filename) & (df["Gesture name"] == gesture_name),
                "End time",
            ].values[0]

            if new_start_time == master_start_time and new_end_time == master_end_time:
                self.statusBar().showMessage(
                    "Info: The start and end times are the same as the previous ones."
                )
                return

            df.loc[
                (df["Filename"] == filename) & (df["Gesture name"] == gesture_name),
                "Start time",
            ] = new_start_time
            df.loc[
                (df["Filename"] == filename) & (df["Gesture name"] == gesture_name),
                "End time",
            ] = new_end_time

            video_path = self.data_folder + "trimmed_video/" + gesture_name + ".mp4"
            csv_path = self.data_folder + "trimmed_csv/" + gesture_name + ".csv"

            if os.path.exists(video_path):
                os.remove(video_path)

            if os.path.exists(csv_path):
                os.remove(csv_path)

            filename_new = self.data_folder + "raw_video/" + filename + ".mp4"

            self.record_update_trim(
                filename_new, new_start_time, new_end_time, gesture_name
            )

            df.to_csv(master_csv_path, index=False)

            self.statusBar().showMessage(
                "Info: The gesture is being updated, please wait!"
            )

        return save_function

    def arrow_left_event(self):
        if not self.check_media_status():
            return
        self.set_position(self.video_slider.value() - 200)

    def arrow_right_event(self):
        if not self.check_media_status():
            return
        self.set_position(self.video_slider.value() + 200)

    def open_video(self):
        video_name, _ = QFileDialog.getOpenFileName(
            self, "Open Movie", "~/Desktop/AAC/annotation/src/data/raw_video/"
        )
        self.video_name = video_name

        if self.video_name != "":
            self.video_player.setMedia(
                QMediaContent(QUrl.fromLocalFile(self.video_name))
            )

            if not self.check_media_status():
                return

            index = self.video_name.rfind("/")
            self.statusbar.showMessage(
                "Info: Playing the video '" + self.video_name[(index + 1) :] + "' ..."
            )
            self.button_play.setEnabled(True)
            self.open_csv()

    def open_csv(self):
        csv_name = self.video_name.replace(".mp4", ".csv").replace(
            "raw_video", "raw_csv"
        )
        self.acc_data = pd.read_csv(csv_name)

        # add id and time columns
        if "Id" not in self.acc_data.columns:
            self.acc_data["Id"] = range(len(self.acc_data))
        if "Time" not in self.acc_data.columns:
            self.acc_data["Time"] = self.acc_data["Id"] / self.frequency

        self.acc_data.to_csv(csv_name, index=False)

        self.final_end_time = self.acc_data["Time"].iloc[-1]

    def check_media_status(self):
        if self.video_player.mediaStatus() == QMediaPlayer.NoMedia:
            self.statusBar().showMessage("Error: No media loaded.")
            return False

        return True

    def play_video(self):
        self.take_screenshot()
        self.curr_playing = False
        if self.video_player_thread != None:
            self.video_player_thread.terminate()

        if not self.check_media_status():
            return
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
        else:
            self.video_player.play()

    def take_screenshot(self):
        print("Taking screenshot")
        pixmap = self.grab()
        pixmap.save("screenshot_annotation.png")

    def update_plot(self, time):
        start_time = max(time - 2, 0)
        end_time = min(time, self.final_end_time)
        if start_time == end_time:
            return

        data = self.acc_data[
            (self.acc_data["Time"] >= start_time) & (self.acc_data["Time"] <= end_time)
        ]

        for curve, column in zip(self.plots, ["acc_x", "acc_y", "acc_z"]):
            y_values = data[column].tolist()
            x_values = np.linspace(start_time, end_time, num=len(y_values))
            curve.setData(x_values, y_values)

    def media_state_changed(self, state):
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.button_play.setIcon(self.icon_pause)
        else:
            self.button_play.setIcon(self.icon_play)

    def position_changed(self, position):
        self.video_slider.setValue(position)
        self.update_plot(position / 1000)
        self.timestampLabel.setText(
            "Time: {}/{}".format(
                round(position / 1000, 1), round(self.video_duration / 1000, 1)
            )
        )

    def duration_changed(self, duration):
        self.video_slider.setRange(0, duration)
        self.video_duration = duration
        self.record_start_time = 0
        self.record_end_time = 0

    def set_position(self, position):
        self.video_player.setPosition(position)

    def error_control(self):
        self.button_play.setEnabled(False)
        self.statusbar.showMessage("Error: An error occured while opening the video.")

    def record_start(self):
        self.video_player.pause()
        self.record_start_time = round(self.video_slider.sliderPosition(), 1)
        if (
            self.record_end_time is not None
            and self.record_end_time != 0
            and self.record_start_time > self.record_end_time
        ):
            self.record_start_time, self.record_end_time = (
                self.record_end_time,
                self.record_start_time,
            )

        self._show_record_time()

    def record_end(self):
        self.video_player.pause()
        self.record_end_time = round(self.video_slider.sliderPosition(), 1)
        if (
            self.record_start_time is not None
            and self.record_start_time > self.record_end_time
        ):
            self.record_start_time, self.record_end_time = (
                self.record_end_time,
                self.record_start_time,
            )

        self._show_record_time()

    def _show_record_time(self):
        if self.record_start_time is not None and self.record_end_time is not None:
            self.statusbar.showMessage(
                "Info: Starting time: ({}), and Ending time: ({}) (Duration: {}).".format(
                    self.record_start_time / 1000,
                    self.record_end_time / 1000,
                    self.video_duration / 1000,
                )
            )

    def _check_duration(self):
        if self.video_name == "":
            self.statusbar.showMessage("Error: Please open a video first.")
        elif self.record_start_time == self.record_end_time:
            self.statusbar.showMessage("Error: Duration can NOT be 0.")
        elif self.record_start_time > self.record_end_time:
            self.statusbar.showMessage(
                "Error: The start time should be earlier than the end time."
            )
        else:
            return True

        return False

    def _check_name(self):
        if self.textbox_register.text() == "":
            self.statusbar.showMessage("Error: Please input the gesture name.")
            return False
        else:
            data_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
            master_csv_path = data_path + "master.csv"

            if os.path.exists(master_csv_path):
                df = pd.read_csv(master_csv_path)
                if (
                    self.textbox_register.text().replace(" ", "_").lower()
                    in df["Gesture name"].values
                ):
                    self.statusbar.showMessage(
                        "Error: The gesture name already exists."
                    )
                    return False
                else:
                    return True
            else:
                return True

    def record_trim_recording(self):
        if self._check_duration() and self._check_name():
            self.statusbar.showMessage("Info: Please wait until the process ends.")
            self.button_annotate.setEnabled(False)
            self.thread = Thread()
            self.is_finished = False
            self.thread.set_params(
                Thread.MSG_TRIM_RECORDING,
                self.video_name,
                self.record_start_time / 1000,
                self.record_end_time / 1000,
                self.textbox_register.text().replace(" ", "_"),
            )
            self.thread.signal_return_value.connect(self.thread_done)
            self.thread.start()
            self.record_clear(1)

    def record_update_trim(self, video_name, start_time, end_time, gesture_name):
        self.thread = Thread()
        self.is_finished = False
        self.thread.set_params(
            Thread.MSG_TRIM_RECORDING,
            video_name,
            start_time,
            end_time,
            gesture_name,
        )

        self.thread.signal_return_value.connect(self.thread_done)
        self.thread.start()
        self.record_clear(1)

    def record_clear(self, event=None):
        self.record_start_time = 0
        self.record_end_time = 0

        if event is None:
            self.statusbar.showMessage(
                "Info: Starting time: ({}), and Ending time: ({}).".format(
                    self.record_start_time, self.record_end_time
                )
            )

    def thread_done(self, return_value, video_name):
        self.button_annotate.setEnabled(True)
        if return_value:
            self.is_finished = True
            self.statusbar.showMessage(
                "Info: The process has done and saved as {}.".format(video_name)
            )
            self.widget_annotations.clear()
            self.populate_annotations()

    def closeEvent(self, event):
        if not self.is_finished:
            self.thread.stop()
        self.video_player.stop()
        event.accept()


