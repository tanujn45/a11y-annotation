from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QAction,
    QLineEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
)
import pyqtgraph as pg
import sys
import pandas as pd
import os
import numpy as np
import warnings
from sklearn.cluster import KMeans
from src.apply_filters import differentitaion, moving_average

warnings.filterwarnings("ignore")


class DetectionWindow(QMainWindow):
    def __init__(self, parent=None):
        super(DetectionWindow, self).__init__(parent)
        self.setWindowTitle("Detection tool")
        self.showFullScreen()
        # self.resize(DetectionWindow.WIN_SIZE[0], DetectionWindow.WIN_SIZE[1])
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveDVDIcon))

        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.video_name = ""
        self.gesture_name = ""
        self.acc_data = None
        self.frequency = 50
        self.final_end_time = 0
        self.kmeans = []
        self.prefix = []
        self.weights = []
        self.combined_data_gestures = None

        self.data_folder = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
        self.trimmed_csv_folder_path = self.data_folder + "trimmed_csv/"
        self.raw_csv_folder_path = self.data_folder + "raw_csv/"

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

            QComboBox {
                background-color: #2a2b2e;
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid black;
            }
            """
        )

        self.widget_video = QVideoWidget()

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.timestampLabel = QLabel("")
        self.statusbar.addPermanentWidget(self.timestampLabel)

        # Action 'Open'
        self.action_open = QAction(QIcon("open.png"), "&Open", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.setStatusTip("Open a video")
        self.action_open.triggered.connect(self.open_video)

        # Menu bar
        self.menu_bar = self.menuBar()
        self.menu_menu = self.menu_bar.addMenu("&Menu")
        self.menu_menu.addAction(self.action_open)

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

        self.model_dropdown = QtWidgets.QComboBox()
        self.model_dropdown.currentIndexChanged.connect(self.model_changed)

        # Main Widget
        self.widget_window = QWidget(self)
        self.setCentralWidget(self.widget_window)

        # Play button and slider (layout_widget)
        self.layout_widget = QHBoxLayout()
        self.layout_widget.setContentsMargins(0, 0, 0, 0)
        self.layout_widget.addWidget(self.button_bb)
        self.layout_widget.addWidget(self.button_play)
        self.layout_widget.addWidget(self.button_ff)
        self.layout_widget.addWidget(self.model_dropdown)

        # Video layout (video_layout_window)
        self.video_layout_window = QVBoxLayout()
        self.video_layout_window.addWidget(self.widget_video)
        self.video_layout_window.addLayout(self.layout_widget)
        self.video_layout_window.addWidget(self.video_slider)

        # Graph and recorded gestures (widget_graph)
        self.widget_graph = pg.plot(title="Accelerometer Data")
        self.plots = [
            self.widget_graph.plot(pen=pg.mkPen(color=("r", "g", "b")[i]))
            for i in range(3)
        ]
        self.widget_graph.setLabel("left", "Acceleration", units="m/s^2")
        self.widget_graph.setLabel("bottom", "Time", units="s")
        self.widget_graph.showGrid(x=True, y=True)
        self.layout_graph_register = QVBoxLayout()
        self.detected_gesture_label = QLabel("Gesture:")
        self.layout_graph_register.setContentsMargins(0, 0, 0, 0)
        self.layout_graph_register.addWidget(self.widget_graph, 5)
        self.layout_graph_register.addWidget(self.detected_gesture_label, 1)

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

        self.n_clusters = 20

        self.apply_filters()
        self.populate_model_dropdown()
        self.model_changed()

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
                self.statusBar.showMessage(
                    "Error: An error occured while opening the video."
                )
                return

            index = self.video_name.rfind("/")
            self.statusbar.showMessage(
                "Info: Playing the video '" + self.video_name[(index + 1) :] + "' ..."
            )
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

    def populate_model_dropdown(self):
        self.model_dropdown.clear()

        data_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/models/"
        files = os.listdir(data_path)
        for file in files:
            if file.endswith(".csv"):
                self.model_dropdown.addItem(file.split(".")[0])

    def model_changed(self):
        curr_model = self.model_dropdown.currentText()
        curr_model_file = (
            "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/models/"
            + curr_model
            + ".csv"
        )

        if not os.path.exists(curr_model_file):
            self.statusbar.showMessage("Error: Model file not found.")
            return

        df = pd.read_csv(curr_model_file)

        self.prefix = df["prefix"].str.split(",").tolist()

        self.weights = [list(map(float, str(x).split(","))) for x in df["weight"]]

        self.get_kmeans()
        self.set_position(0)

    def get_kmeans(self):
        self.combined_data_gestures = self.combine_data()
        self.combined_data_gestures.dropna(inplace=True)
        self.kmeans = []
        for i in range(len(self.prefix)):
            columns = []

            for p in self.prefix[i]:
                columns += [p + "_x", p + "_y", p + "_z"]

            # Apply the KMeans algorithm
            kmeans_columns = self.combined_data_gestures[columns].copy()
            kmean = KMeans(n_clusters=self.n_clusters, random_state=42)
            kmean.fit(kmeans_columns)
            self.combined_data_gestures["cluster_id"] = kmean.labels_
            self.kmeans.append(kmean)

    def normalize(self, result):
        total = sum(result)
        if total == 0:
            return result
        result = [element / total for element in result]
        return result

    def norm_sim(self, cluster1, cluster2):
        return self.longest_common_subsequence(cluster1, cluster2) / max(
            len(cluster1), len(cluster2)
        )

    def longest_common_subsequence(self, cluster1, cluster2):
        m = len(cluster1)
        n = len(cluster2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if cluster1[i - 1] == cluster2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def load_csv(self, file_path):
        data = pd.read_csv(file_path)
        return data

    def combine_data(self):
        self.csv_files = [
            file
            for file in os.listdir(self.trimmed_csv_folder_path)
            if file.endswith(".csv")
        ]
        self.csv_files.sort()
        combined_data = pd.DataFrame()
        for file in self.csv_files:
            file_path = os.path.join(self.trimmed_csv_folder_path, file)
            data = self.load_csv(file_path)
            data["gesture_id"] = file.split(".")[0]
            combined_data = combined_data.append(data)
        return combined_data

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

        result = [0 for _ in range(len(self.csv_files))]
        if start_time > 0 and start_time + 2 <= end_time:
            for i in range(len(self.prefix)):
                columns = []

                for p in self.prefix[i]:
                    columns += [p + "_x", p + "_y", p + "_z"]

                data["cluster_id"] = self.kmeans[i].predict(data[columns])

                result_curr = self.process_data(
                    self.combined_data_gestures, data, self.csv_files
                )
                result = [
                    x + self.weights[i][0] * y for x, y in zip(result, result_curr)
                ]

            result = [round(x, 2) for x in result]
            max_index = np.argmax(result)
            self.detected_gesture_label.setText(
                "Gesture: <font color='green'>"
                + self.csv_files[max_index].split(".")[0].replace("_", " ").capitalize()
                + "</font> (conf "
                + str(result[max_index])
                + ")"
            )

    def process_data(self, combined_data, unknown_data, csv_file):
        result = [0 for _ in range(len(csv_file))]

        for i in range(len(csv_file)):
            cluster1 = combined_data[
                combined_data["gesture_id"] == csv_file[i].split(".")[0]
            ]
            cluster2 = unknown_data
            result[i] = self.norm_sim(
                cluster1["cluster_id"].tolist(),
                cluster2["cluster_id"].tolist(),
            )
        return result

    def apply_filters(self):
        csv_files = [
            file
            for file in os.listdir(self.raw_csv_folder_path)
            if file.endswith(".csv")
        ]

        for file in csv_files:
            file_path = os.path.join(self.raw_csv_folder_path, file)
            data = self.load_csv(file_path)
            if "acc_diff_x" not in data.columns:
                data = differentitaion(data)
            if "acc_ma_x" not in data.columns:
                data = moving_average(data)
            data.to_csv(os.path.join(self.raw_csv_folder_path, file), index=False)

    def arrow_left_event(self):
        if not self.check_media_status():
            return
        self.set_position(self.video_slider.value() - 200)

    def arrow_right_event(self):
        if not self.check_media_status():
            return
        self.set_position(self.video_slider.value() + 200)

    def check_media_status(self):
        if self.video_player.mediaStatus() == QMediaPlayer.NoMedia:
            self.statusBar().showMessage("Error: No media loaded.")
            return False

        return True

    def play_video(self):
        self.take_screenshot()
        if not self.check_media_status():
            return
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
        else:
            self.video_player.play()

    def take_screenshot(self):
        print("Taking screenshot")
        pixmap = self.grab()
        pixmap.save("screenshot_detection.png")

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
        self.statusbar.showMessage("Error: An error occurs while opening the video.")

    def closeEvent(self, event):
        self.video_player.stop()
        event.accept()


if __name__ == "__main__":
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    main_window = DetectionWindow()
    main_window.show()

    app.exec_()
