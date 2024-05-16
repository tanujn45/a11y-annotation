from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph import TextItem
from src.matrix import heatmap_data, similartiy_gesture
import pandas as pd
import os
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import sys


class VisualizationWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VisualizationWindow, self).__init__(parent)
        self.setWindowTitle("Visualization tool")
        self.showFullScreen()
        # self.resize(VisualizationWindow.WIN_SIZE[0], VisualizationWindow.WIN_SIZE[1])
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveDVDIcon))

        # Initialize two video players
        self.video_player_1 = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player_2 = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.record_start_time = None
        self.record_end_time = None
        self.video_name = ""
        self.gesture_name = ""
        self.acc_data = None
        self.frequency = 50
        self.final_end_time = 0
        self.prefix = []
        self.weights = []
        self.something_selected = False

        self.data_folder = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"

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

            QCheckBox {
                margin: 0px;
                padding: 0px;
            }
            """
        )

        # initialize two video widgets
        self.widget_video_1 = QVideoWidget()
        self.widget_video_2 = QVideoWidget()

        # Setting up the statusbar
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.timestampLabel_1 = QLabel("")
        self.statusbar.addPermanentWidget(self.timestampLabel_1)
        self.spaceBetween = QLabel(" | ")
        self.statusbar.addPermanentWidget(self.spaceBetween)
        self.timestampLabel_2 = QLabel("")
        self.statusbar.addPermanentWidget(self.timestampLabel_2)

        # Setup the play icon
        pixmap_play = self.style().standardPixmap(QStyle.SP_MediaPlay)
        painter_play = QPainter(pixmap_play)
        painter_play.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_play.fillRect(pixmap_play.rect(), QColor("white"))
        painter_play.end()
        self.icon_play = QIcon(pixmap_play)

        # Setup the pause icon
        pixmap_pause = self.style().standardPixmap(QStyle.SP_MediaPause)
        painter_pause = QPainter(pixmap_pause)
        painter_pause.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_pause.fillRect(pixmap_pause.rect(), QColor("white"))
        painter_pause.end()
        self.icon_pause = QIcon(pixmap_pause)

        # Setup the forward icon
        pixmap_ff = self.style().standardPixmap(QStyle.SP_MediaSkipForward)
        painter_ff = QPainter(pixmap_ff)
        painter_ff.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_ff.fillRect(pixmap_ff.rect(), QColor("white"))
        painter_ff.end()
        icon_ff = QIcon(pixmap_ff)

        # Setup the backward icon
        pixmap_bb = self.style().standardPixmap(QStyle.SP_MediaSkipBackward)
        painter_bb = QPainter(pixmap_bb)
        painter_bb.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter_bb.fillRect(pixmap_bb.rect(), QColor("white"))
        painter_bb.end()
        icon_bb = QIcon(pixmap_bb)

        # Inititalize the play buttons for videos
        self.button_play_1 = QPushButton()
        self.button_play_1.setIcon(self.icon_play)
        self.button_play_2 = QPushButton()
        self.button_play_2.setIcon(self.icon_play)
        self.button_play_1.clicked.connect(self.play_video_1)
        self.button_play_2.clicked.connect(self.play_video_2)

        # Initialize the forward buttons for videos
        self.button_ff_1 = QPushButton()
        self.button_ff_1.setIcon(icon_ff)
        self.button_ff_2 = QPushButton()
        self.button_ff_2.setIcon(icon_ff)
        self.button_ff_1.clicked.connect(self.arrow_right_event_1)
        self.button_ff_2.clicked.connect(self.arrow_right_event_2)

        # Initialize the backward buttons for videos
        self.button_bb_1 = QPushButton()
        self.button_bb_1.setIcon(icon_bb)
        self.button_bb_2 = QPushButton()
        self.button_bb_2.setIcon(icon_bb)
        self.button_bb_1.clicked.connect(self.arrow_left_event_1)
        self.button_bb_2.clicked.connect(self.arrow_left_event_2)

        # Initialize the video sliders
        self.video_slider_1 = QSlider(Qt.Horizontal)
        self.video_slider_1.setTickInterval(100)
        self.video_slider_1.setRange(0, 0)
        self.video_slider_2 = QSlider(Qt.Horizontal)
        self.video_slider_2.setTickInterval(100)
        self.video_slider_2.setRange(0, 0)
        self.video_slider_1.sliderMoved.connect(self.set_position_1)
        self.video_slider_2.sliderMoved.connect(self.set_position_2)
        self.video_duration_1 = 0
        self.video_duration_2 = 0

        # Main Widget
        self.widget_window = QWidget(self)
        self.setCentralWidget(self.widget_window)

        # Play, FF, BB buttons and slider for video 1 (layout_widget_1)
        self.layout_widget_1 = QHBoxLayout()
        self.layout_widget_1.setContentsMargins(0, 0, 0, 0)
        self.layout_widget_1.addWidget(self.button_bb_1)
        self.layout_widget_1.addWidget(self.button_play_1)
        self.layout_widget_1.addWidget(self.button_ff_1)

        # Play, FF, BB buttons and slider for video 2 (layout_widget_2)
        self.layout_widget_2 = QHBoxLayout()
        self.layout_widget_2.setContentsMargins(0, 0, 0, 0)
        self.layout_widget_2.addWidget(self.button_bb_2)
        self.layout_widget_2.addWidget(self.button_play_2)
        self.layout_widget_2.addWidget(self.button_ff_2)

        # Video layout (video_layout_window)
        self.video_layout_window = QVBoxLayout()
        self.video_layout_window.addWidget(self.widget_video_1)
        self.video_layout_window.addWidget(self.video_slider_1)
        self.video_layout_window.addLayout(self.layout_widget_1)
        self.video_layout_window.addWidget(self.widget_video_2)
        self.video_layout_window.addWidget(self.video_slider_2)
        self.video_layout_window.addLayout(self.layout_widget_2)

        # Heatmap plot
        # self.heatmap_plot = pg.plot(title="Heatmap")
        # self.img = pg.ImageItem()
        # self.heatmap_plot.addItem(self.img)
        # self.img.setLookupTable(pg.colormap.get("CET-D1").getLookupTable())
        plt.style.use("dark_background")
        self.canvas = FigureCanvas(plt.figure())
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Dropdowns to select the gesture: Template and gesture to check
        self.gesture_dropdown_1 = QtWidgets.QComboBox()
        self.gesture_dropdown_1.setFixedWidth(150)
        self.gesture_dropdown_1.currentIndexChanged.connect(self.on_dropdown_change_1)
        self.gesture_dropdown_2 = QtWidgets.QComboBox()
        self.gesture_dropdown_2.setFixedWidth(150)
        self.gesture_dropdown_2.currentIndexChanged.connect(self.on_dropdown_change_2)
        self.check_similarity_button = QPushButton("Check similarity")
        self.check_similarity_button.clicked.connect(self.update_similarity)
        self.layout_dropdown = QHBoxLayout()
        self.layout_dropdown.addWidget(self.gesture_dropdown_1, 1)
        self.layout_dropdown.addWidget(self.gesture_dropdown_2, 1)
        self.layout_dropdown.addWidget(self.check_similarity_button, 1)
        self.populate_dropdown()

        # Checkboxes to set filters
        self.checkbox_acc = QtWidgets.QCheckBox("acc")
        self.checkbox_gyro = QtWidgets.QCheckBox("gyro")
        self.checkbox_diff = QtWidgets.QCheckBox("diff")
        self.checkbox_ma = QtWidgets.QCheckBox("moving average")

        # Set fixed width for checkboxes
        self.checkbox_acc.setFixedWidth(150)
        self.checkbox_gyro.setFixedWidth(150)
        self.checkbox_diff.setFixedWidth(150)
        self.checkbox_ma.setFixedWidth(150)

        # Connect checkboxes to update_plots
        self.checkbox_acc.stateChanged.connect(self.update_plots)
        self.checkbox_gyro.stateChanged.connect(self.update_plots)
        self.checkbox_diff.stateChanged.connect(self.update_plots)
        self.checkbox_ma.stateChanged.connect(self.update_plots)

        # X label texts
        self.circle_x_acc_text = QLabel("x")
        self.circle_x_gyro_text = QLabel("x")
        self.circle_x_diff_text = QLabel("x")
        self.circle_x_ma_text = QLabel("x")

        # Y label texts
        self.circle_y_acc_text = QLabel("y")
        self.circle_y_gyro_text = QLabel("y")
        self.circle_y_diff_text = QLabel("y")
        self.circle_y_ma_text = QLabel("y")

        # Z label texts
        self.circle_z_acc_text = QLabel("z")
        self.circle_z_gyro_text = QLabel("z")
        self.circle_z_diff_text = QLabel("z")
        self.circle_z_ma_text = QLabel("z")

        # Set fixed width for x label texts
        self.circle_x_acc_text.setFixedWidth(10)
        self.circle_x_gyro_text.setFixedWidth(10)
        self.circle_x_diff_text.setFixedWidth(10)
        self.circle_x_ma_text.setFixedWidth(10)

        # Set fixed width for y label texts
        self.circle_y_acc_text.setFixedWidth(10)
        self.circle_y_gyro_text.setFixedWidth(10)
        self.circle_y_diff_text.setFixedWidth(10)
        self.circle_y_ma_text.setFixedWidth(10)

        # Set fixed width for z label texts
        self.circle_z_acc_text.setFixedWidth(10)
        self.circle_z_gyro_text.setFixedWidth(10)
        self.circle_z_diff_text.setFixedWidth(10)
        self.circle_z_ma_text.setFixedWidth(10)

        self.circle_x_acc = QLabel()
        self.circle_x_gyro = QLabel()
        self.circle_x_diff = QLabel()
        self.circle_x_ma = QLabel()

        self.circle_y_acc = QLabel()
        self.circle_y_gyro = QLabel()
        self.circle_y_diff = QLabel()
        self.circle_y_ma = QLabel()

        self.circle_z_acc = QLabel()
        self.circle_z_gyro = QLabel()
        self.circle_z_diff = QLabel()
        self.circle_z_ma = QLabel()

        self.circle_x_acc.setFixedSize(10, 10)
        self.circle_x_gyro.setFixedSize(10, 10)
        self.circle_x_diff.setFixedSize(10, 10)
        self.circle_x_ma.setFixedSize(10, 10)

        self.circle_y_acc.setFixedSize(10, 10)
        self.circle_y_gyro.setFixedSize(10, 10)
        self.circle_y_diff.setFixedSize(10, 10)
        self.circle_y_ma.setFixedSize(10, 10)

        self.circle_z_acc.setFixedSize(10, 10)
        self.circle_z_gyro.setFixedSize(10, 10)
        self.circle_z_diff.setFixedSize(10, 10)
        self.circle_z_ma.setFixedSize(10, 10)

        self.circle_x_acc.setStyleSheet("background-color: red; border-radius: 5px;")
        self.circle_x_gyro.setStyleSheet("background-color: cyan; border-radius: 5px;")
        self.circle_x_diff.setStyleSheet(
            "background-color: orange; border-radius: 5px;"
        )
        self.circle_x_ma.setStyleSheet("background-color: #FF4500; border-radius: 5px;")

        self.circle_y_acc.setStyleSheet("background-color: green; border-radius: 5px;")
        self.circle_y_gyro.setStyleSheet(
            "background-color: magenta; border-radius: 5px;"
        )
        self.circle_y_diff.setStyleSheet(
            "background-color: purple; border-radius: 5px;"
        )
        self.circle_y_ma.setStyleSheet("background-color: #32CD32; border-radius: 5px;")

        self.circle_z_acc.setStyleSheet("background-color: blue; border-radius: 5px;")
        self.circle_z_gyro.setStyleSheet(
            "background-color: yellow; border-radius: 5px;"
        )
        self.circle_z_diff.setStyleSheet("background-color: teal; border-radius: 5px;")
        self.circle_z_ma.setStyleSheet("background-color: #BA55D3; border-radius: 5px;")

        self.layout_circles_acc = QHBoxLayout()
        self.layout_circles_gyro = QHBoxLayout()
        self.layout_circles_diff = QHBoxLayout()
        self.layout_circles_ma = QHBoxLayout()

        self.layout_circles_acc.addWidget(self.circle_x_acc)
        self.layout_circles_gyro.addWidget(self.circle_x_gyro)
        self.layout_circles_diff.addWidget(self.circle_x_diff)
        self.layout_circles_ma.addWidget(self.circle_x_ma)

        self.layout_circles_acc.addWidget(self.circle_x_acc_text)
        self.layout_circles_gyro.addWidget(self.circle_x_gyro_text)
        self.layout_circles_diff.addWidget(self.circle_x_diff_text)
        self.layout_circles_ma.addWidget(self.circle_x_ma_text)

        self.layout_circles_acc.addWidget(self.circle_y_acc)
        self.layout_circles_gyro.addWidget(self.circle_y_gyro)
        self.layout_circles_diff.addWidget(self.circle_y_diff)
        self.layout_circles_ma.addWidget(self.circle_y_ma)

        self.layout_circles_acc.addWidget(self.circle_y_acc_text)
        self.layout_circles_gyro.addWidget(self.circle_y_gyro_text)
        self.layout_circles_diff.addWidget(self.circle_y_diff_text)
        self.layout_circles_ma.addWidget(self.circle_y_ma_text)

        self.layout_circles_acc.addWidget(self.circle_z_acc)
        self.layout_circles_gyro.addWidget(self.circle_z_gyro)
        self.layout_circles_diff.addWidget(self.circle_z_diff)
        self.layout_circles_ma.addWidget(self.circle_z_ma)

        self.layout_circles_acc.addWidget(self.circle_z_acc_text)
        self.layout_circles_gyro.addWidget(self.circle_z_gyro_text)
        self.layout_circles_diff.addWidget(self.circle_z_diff_text)
        self.layout_circles_ma.addWidget(self.circle_z_ma_text)

        self.acc_text = QLineEdit()
        self.gyro_text = QLineEdit()
        self.diff_text = QLineEdit()
        self.ma_text = QLineEdit()

        self.acc_text.setPlaceholderText("Weight")
        self.gyro_text.setPlaceholderText("Weight")
        self.diff_text.setPlaceholderText("Weight")
        self.ma_text.setPlaceholderText("Weight")

        self.acc_text.setFixedWidth(120)
        self.gyro_text.setFixedWidth(120)
        self.diff_text.setFixedWidth(120)
        self.ma_text.setFixedWidth(120)

        self.layout_checkbox_acc = QHBoxLayout()
        self.layout_checkbox_gyro = QHBoxLayout()
        self.layout_checkbox_diff = QHBoxLayout()
        self.layout_checkbox_ma = QHBoxLayout()

        self.layout_checkbox_acc.setContentsMargins(0, 0, 0, 0)
        self.layout_checkbox_gyro.setContentsMargins(0, 0, 0, 0)
        self.layout_checkbox_diff.setContentsMargins(0, 0, 0, 0)
        self.layout_checkbox_ma.setContentsMargins(0, 0, 0, 0)

        self.layout_checkbox_acc.addWidget(self.checkbox_acc)
        self.layout_checkbox_gyro.addWidget(self.checkbox_gyro)
        self.layout_checkbox_diff.addWidget(self.checkbox_diff)
        self.layout_checkbox_ma.addWidget(self.checkbox_ma)

        self.layout_checkbox_acc.addWidget(self.acc_text)
        self.layout_checkbox_gyro.addWidget(self.gyro_text)
        self.layout_checkbox_diff.addWidget(self.diff_text)
        self.layout_checkbox_ma.addWidget(self.ma_text)

        self.layout_checkbox_acc.addLayout(self.layout_circles_acc)
        self.layout_checkbox_gyro.addLayout(self.layout_circles_gyro)
        self.layout_checkbox_diff.addLayout(self.layout_circles_diff)
        self.layout_checkbox_ma.addLayout(self.layout_circles_ma)

        self.layout_checkbox = QVBoxLayout()
        self.layout_checkbox.addLayout(self.layout_checkbox_acc)
        self.layout_checkbox.addLayout(self.layout_checkbox_gyro)
        self.layout_checkbox.addLayout(self.layout_checkbox_diff)
        self.layout_checkbox.addLayout(self.layout_checkbox_ma)

        # Heatmap generate button
        self.heatmap_label = QLabel("Generate heatmap with this combination:")
        self.heatmap_button = QPushButton("Compare All")
        self.heatmap_button.clicked.connect(self.update_heatmap)
        self.layout_heatmap_generate = QHBoxLayout()
        self.layout_heatmap_generate.addWidget(self.heatmap_label)
        self.layout_heatmap_generate.addWidget(self.heatmap_button)

        # Save the model button
        self.save_model_label = QLabel("Save the model:")
        self.save_model_input = QLineEdit()
        self.save_model_input.setPlaceholderText("Name")
        self.save_model_button = QPushButton("Save")
        self.save_model_button.clicked.connect(self.save_model)
        self.save_model_layout = QHBoxLayout()
        self.load_model_dropdown = QtWidgets.QComboBox()
        self.load_model_dropdown.currentIndexChanged.connect(self.load_model)
        self.save_model_layout.addWidget(self.load_model_dropdown)
        self.save_model_layout.addWidget(self.save_model_label)
        self.save_model_layout.addWidget(self.save_model_input)
        self.save_model_layout.addWidget(self.save_model_button)

        # Similarity between two gestures
        self.similarity_label = QLabel(
            "Choose template & comparision gesture, set config"
        )

        self.layout_visualize = QGridLayout()

        self.layout_visualize.addWidget(self.canvas, 0, 0)

        # Add the other widgets to the grid layout
        self.layout_visualize.addLayout(self.layout_dropdown, 1, 0)
        self.layout_visualize.addWidget(self.similarity_label, 2, 0)
        self.layout_visualize.addLayout(self.layout_checkbox, 3, 0)
        self.layout_visualize.addLayout(self.layout_heatmap_generate, 4, 0)
        self.layout_visualize.addLayout(self.save_model_layout, 5, 0)

        # # Visualize data layout (layout_visualize)
        # self.layout_visualize = QVBoxLayout()
        # self.layout_visualize.addWidget(self.canvas)
        # self.layout_visualize.addLayout(self.layout_dropdown)
        # self.layout_visualize.addWidget(self.similarity_label)
        # self.layout_visualize.addLayout(self.layout_checkbox)
        # self.layout_visualize.addLayout(self.layout_heatmap_generate)
        # self.layout_visualize.addLayout(self.save_model_layout)

        # Graph plot for video 1 (widget_graph_1)
        self.widget_graph_1 = pg.plot(title="Accelerometer Data")
        self.plots_1 = [
            self.widget_graph_1.plot(pen=pg.mkPen(color=("r", "g", "b")[i]))
            for i in range(3)
        ]
        self.widget_graph_1.setLabel("left", "Acceleration", units="m/s^2")
        self.widget_graph_1.setLabel("bottom", "Time", units="s")
        self.widget_graph_1.showGrid(x=True, y=True)
        self.tempViewBox_1 = None

        # Graph plot for video 2 (widget_graph_2)
        self.widget_graph_2 = pg.plot(title="Accelerometer Data")
        self.plots_2 = [
            self.widget_graph_2.plot(pen=pg.mkPen(color=("r", "g", "b")[i]))
            for i in range(3)
        ]
        self.widget_graph_2.setLabel("left", "Acceleration", units="m/s^2")
        self.widget_graph_2.setLabel("bottom", "Time", units="s")
        self.widget_graph_2.showGrid(x=True, y=True)
        self.tempViewBox_2 = None

        # Plot layout (layout_plots)
        self.layout_plot = QVBoxLayout()
        # self.widget_graph_1.setFixedWidth(450)
        # self.widget_graph_2.setFixedWidth(450)
        self.layout_plot.addWidget(self.widget_graph_1)
        self.layout_plot.addWidget(self.widget_graph_2)

        # Main layout
        self.layout_window = QHBoxLayout()
        self.layout_window.addLayout(self.video_layout_window, 1)
        self.layout_window.addLayout(self.layout_plot, 2)
        self.layout_window.addLayout(self.layout_visualize, 1)

        # Window layout
        self.widget_window.setLayout(self.layout_window)

        # Initialize the video player 1
        self.video_player_1.setVideoOutput(self.widget_video_1)
        self.video_player_1.setNotifyInterval(100)
        self.video_player_1.stateChanged.connect(self.media_state_changed_1)
        self.video_player_1.positionChanged.connect(self.position_changed_1)
        self.video_player_1.durationChanged.connect(self.duration_changed_1)
        self.video_player_1.mediaStatusChanged.connect(self.loop_videos)
        self.video_player_1.error.connect(self.error_control_1)

        # Initialize the video player 2
        self.video_player_2.setVideoOutput(self.widget_video_2)
        self.video_player_2.setNotifyInterval(100)
        self.video_player_2.stateChanged.connect(self.media_state_changed_2)
        self.video_player_2.positionChanged.connect(self.position_changed_2)
        self.video_player_2.durationChanged.connect(self.duration_changed_2)
        self.video_player_2.mediaStatusChanged.connect(self.loop_videos)
        self.video_player_2.error.connect(self.error_control_2)

        self.populate_model_dropdown()

    def load_model(self, index):
        if index == 0:
            return

        self.checkbox_acc.setChecked(False)
        self.checkbox_diff.setChecked(False)
        self.checkbox_ma.setChecked(False)
        self.acc_text.setText("")
        self.diff_text.setText("")
        self.ma_text.setText("")

        model_name = self.load_model_dropdown.currentText()
        model_path = self.data_folder + "models/" + model_name + ".csv"

        if not os.path.exists(model_path):
            self.statusbar.showMessage("Error: Model does not exist.")
            return

        with open(model_path, "r") as f:
            lines = f.readlines()
            for i in range(1, len(lines)):
                line = lines[i].split(",")
                prefix = line[0]
                weight = line[1]
                if prefix == "acc":
                    self.checkbox_acc.setChecked(True)
                    self.acc_text.setText(weight)
                elif prefix == "acc_diff":
                    self.checkbox_diff.setChecked(True)
                    self.diff_text.setText(weight)
                elif prefix == "acc_ma":
                    self.checkbox_ma.setChecked(True)
                    self.ma_text.setText(weight)

        self.statusbar.showMessage("Info: Model loaded successfully.")

    def populate_model_dropdown(self):
        self.load_model_dropdown.clear()
        self.load_model_dropdown.addItem("Load model")
        model_folder_path = self.data_folder + "models/"
        if not os.path.exists(model_folder_path):
            return

        for model in os.listdir(model_folder_path):
            self.load_model_dropdown.addItem(model.replace(".csv", ""))

    def save_model(self):
        if not self.config_check():
            return

        model_name = self.save_model_input.text()
        if model_name == "":
            self.statusbar.showMessage("Error: Please enter the model name.")
            return

        model_folder_path = self.data_folder + "models/"
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        model_path = model_folder_path + model_name + ".csv"
        if os.path.exists(model_path):
            self.statusbar.showMessage("Error: Model already exists.")
            return

        with open(model_path, "w") as f:
            f.write("prefix,weight\n")
            for i in range(len(self.prefix)):
                f.write(self.prefix[i][0] + "," + str(self.weights[i][0]) + "\n")

        self.statusbar.showMessage("Info: Model saved successfully.")

    def loop_videos(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if (
                not self.check_media_status_1()
                or self.video_player_1.state() == QMediaPlayer.PausedState
            ):
                self.video_player_2.play()
                return
            if (
                not self.check_media_status_2()
                or self.video_player_2.state() == QMediaPlayer.PausedState
            ):
                self.video_player_1.play()
                return
            if (
                self.video_player_1.mediaStatus() == QMediaPlayer.EndOfMedia
                and self.video_player_2.mediaStatus() == QMediaPlayer.EndOfMedia
            ):
                self.video_player_1.play()
                self.video_player_2.play()

    def populate_dropdown(self):
        self.gesture_dropdown_1.clear()
        self.gesture_dropdown_1.addItem("Select template gesture")

        self.gesture_dropdown_2.clear()
        self.gesture_dropdown_2.addItem("Select gesture to compare")

        data_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
        master_csv_path = data_path + "master.csv"

        if os.path.exists(master_csv_path):
            df = pd.read_csv(master_csv_path)
            for index, gesture in df.iterrows():
                self.gesture_dropdown_1.addItem(gesture["Gesture name"])
                self.gesture_dropdown_2.addItem(gesture["Gesture name"])

    def on_dropdown_change_1(self, index):
        if index == 0:
            # @dev: Need to clear the video when index is 0
            return

        gesture_name = self.gesture_dropdown_1.currentText()
        trimmed_video_path = self.data_folder + "trimmed_video/" + gesture_name + ".mp4"

        self.statusbar.showMessage(
            "Info: Loading the gesture '" + gesture_name + "' ..."
        )

        self.video_player_1.setMedia(
            QMediaContent(QUrl.fromLocalFile(trimmed_video_path))
        )

        if not self.check_media_status_1():
            return

        self.button_play_1.setEnabled(True)
        if (
            self.check_media_status_2()
            and self.video_player_2.state() == QMediaPlayer.PlayingState
        ):
            self.set_position_2(0)
        self.video_player_1.play()

        self.update_plots()

    def on_dropdown_change_2(self, index):
        if index == 0:
            # @dev: Need to clear the video when index is 0
            return

        gesture_name = self.gesture_dropdown_2.currentText()
        trimmed_video_path = self.data_folder + "trimmed_video/" + gesture_name + ".mp4"

        self.statusbar.showMessage(
            "Info: Loading the gesture '" + gesture_name + "' ..."
        )

        self.video_player_2.setMedia(
            QMediaContent(QUrl.fromLocalFile(trimmed_video_path))
        )

        if not self.check_media_status_2():
            return

        self.button_play_1.setEnabled(True)
        if (
            self.check_media_status_1()
            and self.video_player_1.state() == QMediaPlayer.PlayingState
        ):
            self.set_position_1(0)
        self.video_player_2.play()

        self.update_plots()

    def update_similarity(self):
        gesture_name_1 = self.gesture_dropdown_1.currentText()
        gesture_name_2 = self.gesture_dropdown_2.currentText()

        if (
            gesture_name_1 == "Select template gesture"
            or gesture_name_2 == "Select gesture to compare"
        ):
            self.statusbar.showMessage("Error: Please select both gestures.")
            return

        if not self.config_check():
            return

        similarity = similartiy_gesture(
            self.prefix, self.weights, gesture_name_1, gesture_name_2
        )

        self.statusbar.showMessage("Info: Similarity updated successfully.")
        self.similarity_label.setText("Similarity: " + str(similarity))

    def open_csv_1(self, gesture_name):
        self.widget_graph_1.clear()
        if self.tempViewBox_1:
            self.tempViewBox_1.clear()
            self.tempViewBox_1 = None

        csv_path = self.data_folder + "trimmed_csv/" + gesture_name + ".csv"
        data = pd.read_csv(csv_path)

        prefix = []
        colors = []

        prefix_to_color = {
            "acc": ["r", "g", "b"],
            "gyro": ["c", "m", "y"],
            "acc_diff": ["#FFA500", "#800080", "#008080"],
            "acc_ma": ["#FF4500", "#32CD32", "#BA55D3"],
        }

        for checkbox, prefixes in zip(
            [
                self.checkbox_acc,
                self.checkbox_gyro,
                self.checkbox_diff,
                self.checkbox_ma,
            ],
            ["acc", "gyro", "acc_diff", "acc_ma"],
        ):
            if checkbox.isChecked():
                prefix += [f"{prefixes}_x", f"{prefixes}_y", f"{prefixes}_z"]
                colors += prefix_to_color[prefixes]

        self.plots_1 = [
            self.widget_graph_1.plot(pen=pg.mkPen(color=color)) for color in colors
        ]

        x_values = data["Time"].tolist()
        gyro_colors = {"gyro_x": "c", "gyro_y": "m", "gyro_z": "y"}

        self.tempViewBox_1 = pg.ViewBox()
        self.widget_graph_1.showAxis("right")
        self.widget_graph_1.scene().addItem(self.tempViewBox_1)
        self.widget_graph_1.getAxis("right").linkToView(self.tempViewBox_1)
        self.tempViewBox_1.setXLink(self.widget_graph_1)
        self.widget_graph_1.getAxis("right").setLabel("Gyroscope")

        def updateViews():
            self.tempViewBox_1.setGeometry(
                self.widget_graph_1.getViewBox().sceneBoundingRect()
            )
            self.tempViewBox_1.linkedViewChanged(
                self.widget_graph_1.getViewBox(), self.tempViewBox_1.XAxis
            )

        updateViews()
        self.widget_graph_1.getViewBox().sigResized.connect(updateViews)

        for curve, column in zip(self.plots_1, prefix):
            y_values = data[column].tolist()
            if "gyro" in column:
                self.tempViewBox_1.addItem(
                    pg.PlotCurveItem(x_values, y_values, pen=gyro_colors[column])
                )
            else:
                curve.setData(x_values, y_values)

    def open_csv_2(self, gesture_name):
        self.widget_graph_2.clear()
        if self.tempViewBox_2:
            self.tempViewBox_2.clear()
            self.tempViewBox_2 = None

        csv_path = self.data_folder + "trimmed_csv/" + gesture_name + ".csv"
        data = pd.read_csv(csv_path)

        prefix = []
        colors = []

        prefix_to_color = {
            "acc": ["r", "g", "b"],
            "gyro": ["c", "m", "y"],
            "acc_diff": ["#FFA500", "#800080", "#008080"],
            "acc_ma": ["#FF4500", "#32CD32", "#BA55D3"],
        }

        for checkbox, prefixes in zip(
            [
                self.checkbox_acc,
                self.checkbox_gyro,
                self.checkbox_diff,
                self.checkbox_ma,
            ],
            ["acc", "gyro", "acc_diff", "acc_ma"],
        ):
            if checkbox.isChecked():
                prefix += [f"{prefixes}_x", f"{prefixes}_y", f"{prefixes}_z"]
                colors += prefix_to_color[prefixes]

        self.plots_2 = [
            self.widget_graph_2.plot(pen=pg.mkPen(color=color)) for color in colors
        ]

        x_values = data["Time"].tolist()
        gyro_colors = {"gyro_x": "c", "gyro_y": "m", "gyro_z": "y"}

        self.tempViewBox_2 = pg.ViewBox()
        self.widget_graph_2.showAxis("right")
        self.widget_graph_2.scene().addItem(self.tempViewBox_2)
        self.widget_graph_2.getAxis("right").linkToView(self.tempViewBox_2)
        self.tempViewBox_2.setXLink(self.widget_graph_2)
        self.widget_graph_2.getAxis("right").setLabel("Gyroscope")

        def updateViews():
            self.tempViewBox_2.setGeometry(
                self.widget_graph_2.getViewBox().sceneBoundingRect()
            )
            self.tempViewBox_2.linkedViewChanged(
                self.widget_graph_2.getViewBox(), self.tempViewBox_2.XAxis
            )

        updateViews()
        self.widget_graph_2.getViewBox().sigResized.connect(updateViews)

        for curve, column in zip(self.plots_2, prefix):
            y_values = data[column].tolist()
            if "gyro" in column:
                self.tempViewBox_2.addItem(
                    pg.PlotCurveItem(x_values, y_values, pen=gyro_colors[column])
                )
            else:
                curve.setData(x_values, y_values)

    def arrow_left_event_1(self):
        if not self.check_media_status_1():
            return
        self.set_position_1(self.video_slider_1.value() - 200)

    def arrow_right_event_1(self):
        if not self.check_media_status_1():
            return
        self.set_position_1(self.video_slider_1.value() + 200)

    def arrow_left_event_2(self):
        if not self.check_media_status_2():
            return
        self.set_position_2(self.video_slider_2.value() - 200)

    def arrow_right_event_2(self):
        if not self.check_media_status_2():
            return
        self.set_position_2(self.video_slider_2.value() + 200)

    def check_media_status_1(self):
        if self.video_player_1.mediaStatus() == QMediaPlayer.NoMedia:
            self.statusBar().showMessage("Error: No media loaded.")
            return False

        return True

    def check_media_status_2(self):
        if self.video_player_2.mediaStatus() == QMediaPlayer.NoMedia:
            self.statusBar().showMessage("Error: No media loaded.")
            return False

        return True

    def play_video_1(self):
        if not self.check_media_status_1():
            return
        if self.video_player_1.state() == QMediaPlayer.PlayingState:
            self.video_player_1.pause()
        else:
            self.video_player_1.play()

    def play_video_2(self):
        if not self.check_media_status_2():
            return
        if self.video_player_2.state() == QMediaPlayer.PlayingState:
            self.video_player_2.pause()
        else:
            self.video_player_2.play()

    def loop_video_1(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.video_player_1.play()

    def loop_video_2(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.video_player_2.play()

    def update_plots(self):
        if self.checkbox_acc.isChecked():
            self.acc_text.setEnabled(True)
            self.acc_text.setFocusPolicy(Qt.ClickFocus)

        if self.checkbox_gyro.isChecked():
            self.gyro_text.setEnabled(True)
            self.gyro_text.setFocus()

        if self.checkbox_diff.isChecked():
            self.diff_text.setEnabled(True)
            self.diff_text.setFocus()

        if self.checkbox_ma.isChecked():
            self.ma_text.setEnabled(True)
            self.ma_text.setFocus()

        if not self.gesture_dropdown_1.currentText() == "Select template gesture":
            self.widget_graph_1.clear()
            self.open_csv_1(self.gesture_dropdown_1.currentText())
        if not self.gesture_dropdown_2.currentText() == "Select gesture to compare":
            self.widget_graph_2.clear()
            self.open_csv_2(self.gesture_dropdown_2.currentText())

    def config_check(self):
        self.prefix = []
        self.weights = []
        self.something_selected = False

        if self.checkbox_acc.isChecked():
            if self.acc_text.text() == "":
                self.statusbar.showMessage(
                    "Error: Please enter the weight for acc. (between 0 and 1)"
                )
                return False
            else:
                self.something_selected = True
                self.weights.append([float(self.acc_text.text())])
                self.prefix.append(["acc"])

        if self.checkbox_gyro.isChecked():
            if self.gyro_text.text() == "":
                self.statusbar.showMessage(
                    "Error: Please enter the weight for gyro. (between 0 and 1)"
                )
                return False
            else:
                self.something_selected = True
                self.weights.append([float(self.gyro_text.text())])
                self.prefix.append(["gyro"])

        if self.checkbox_diff.isChecked():
            if self.diff_text.text() == "":
                self.statusbar.showMessage(
                    "Error: Please enter the weight for diff. (between 0 and 1)"
                )
                return False
            else:
                self.something_selected = True
                self.weights.append([float(self.diff_text.text())])
                self.prefix.append(["acc_diff"])

        if self.checkbox_ma.isChecked():
            if self.ma_text.text() == "":
                self.statusbar.showMessage(
                    "Error: Please enter the weight for moving average. (between 0 and 1)"
                )
                return False
            else:
                self.something_selected = True
                self.weights.append([float(self.ma_text.text())])
                self.prefix.append(["acc_ma"])

        if not self.something_selected:
            self.statusbar.showMessage("Error: Please select at least one filter.")
            return False

        total_weight = sum([sum(w) for w in self.weights])
        if total_weight != 1:
            self.statusbar.showMessage("Error: Total of all the weights should be 1.")
            return False

        return True

    # def update_heatmap(self):
    #     if not self.config_check():
    #         return

    #     if len(self.prefix) != 0:
    #         matrix, gesture_names = heatmap_data(self.prefix, self.weights)
    #         gesture_names = [name.split(".")[0] for name in gesture_names]
    #         matrix = np.array(matrix)
    #         matrix = np.flipud(matrix)

    #         plot_item = self.heatmap_plot.getPlotItem()
    #         plot_item.clear()

    #         # Calculate the min and max values for the entire dataset
    #         min_val, max_val = np.min(matrix), np.max(matrix)
    #         print(min_val, max_val)

    #         # New code added to set the colormap
    #         color_map = pg.colormap.get("viridis", source="matplotlib")
    #         lookup_table = color_map.getLookupTable(min_val, max_val, alpha=False)

    #         # Set the lookup table and levels
    #         self.img.setLookupTable(lookup_table)
    #         self.img.setLevels([min_val, max_val])

    #         # Set the heatmap data
    #         self.img.setImage(matrix)
    #         plot_item.addItem(self.img)

    #         plot_item.showAxis("top", show=True)
    #         plot_item.showAxis("right", show=True)

    #         # Set the ticks on the x and y axes
    #         x_ticks = [(i + 0.5, name) for i, name in enumerate(gesture_names)]
    #         y_ticks = [
    #             (matrix.shape[0] - i - 0.5, name)
    #             for i, name in enumerate(gesture_names)
    #         ]
    #         plot_item.getAxis("top").setTicks([x_ticks])
    #         plot_item.getAxis("left").setTicks([y_ticks])

    #         plot_item.getAxis("bottom").setTicks([])
    #         plot_item.getAxis("right").setTicks([])

    #         # Add text to each cell
    #         for i in range(matrix.shape[0]):
    #             for j in range(matrix.shape[1]):
    #                 text = TextItem(text=str(matrix[i, j]), color="w")
    #                 text.setPos(j + 0.3, i + 0.65)
    #                 plot_item.addItem(text)

    #         self.statusbar.showMessage("Info: Heatmap updated successfully.")

    def update_heatmap(self):
        if not self.config_check():
            return

        if len(self.prefix) != 0:
            matrix, gesture_names = heatmap_data(self.prefix, self.weights)
            gesture_names = [name.split(".")[0] for name in gesture_names]
            matrix = np.array(matrix)
            # matrix = np.flipud(matrix)

            self.canvas.figure.clear()
            self.canvas.figure.subplots_adjust(bottom=0.1, top=0.80)
            ax = self.canvas.figure.add_subplot()
            ax.set_facecolor("black")

            heatmap = ax.imshow(matrix, cmap="viridis")

            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    ax.text(j, i, matrix[i, j], ha="center", va="center", color="w")

            # Configure the plot
            ax.xaxis.tick_top()
            ax.set_xticks(np.arange(matrix.shape[1]))
            ax.set_yticks(np.arange(matrix.shape[0]))
            ax.set_xticklabels(gesture_names, rotation=45)
            ax.set_yticklabels(gesture_names[::-1])
            # ax.set_xlabel("X")
            # ax.set_ylabel("Y")
            # ax.set_title("Heatmap")

            # Redraw the canvas
            self.canvas.draw()

    def media_state_changed_1(self, state):
        if self.video_player_1.state() == QMediaPlayer.PlayingState:
            self.button_play_1.setIcon(self.icon_pause)
        else:
            self.button_play_1.setIcon(self.icon_play)

    def media_state_changed_2(self, state):
        if self.video_player_2.state() == QMediaPlayer.PlayingState:
            self.button_play_2.setIcon(self.icon_pause)
        else:
            self.button_play_2.setIcon(self.icon_play)

    def position_changed_1(self, position):
        self.video_slider_1.setValue(position)
        self.timestampLabel_1.setText(
            "Time Video_1: {}/{}".format(
                round(position / 1000, 1), round(self.video_duration_1 / 1000, 1)
            )
        )

    def position_changed_2(self, position):
        self.video_slider_2.setValue(position)
        self.timestampLabel_2.setText(
            "Time Video_2: {}/{}".format(
                round(position / 1000, 1), round(self.video_duration_2 / 1000, 1)
            )
        )

    def duration_changed_1(self, duration):
        self.video_slider_1.setRange(0, duration)
        self.video_duration_1 = duration

    def duration_changed_2(self, duration):
        self.video_slider_2.setRange(0, duration)
        self.video_duration_2 = duration

    def set_position_1(self, position):
        self.video_player_1.setPosition(position)

    def set_position_2(self, position):
        self.video_player_2.setPosition(position)

    def error_control_1(self):
        self.button_play_1.setEnabled(False)
        self.statusbar.showMessage("Error: An error occured while opening the video.")

    def error_control_2(self):
        self.button_play_2.setEnabled(False)
        self.statusbar.showMessage("Error: An error occured while opening the video.")

    def closeEvent(self, event):
        self.video_player_1.stop()
        self.video_player_2.stop()
        event.accept()

