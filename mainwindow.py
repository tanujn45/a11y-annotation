from PyQt5 import QtCore, QtWidgets
from annotation import AnnotationWindow
from visualization import VisualizationWindow
from detection import DetectionWindow
import sys
from PyQt5 import QtGui


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AAC Data Analytics tool")
        self.showFullScreen()
        # sizePolicy = QtWidgets.QSizePolicy(
        #     QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred
        # )
        # self.setSizePolicy(sizePolicy)

        self.howtouse_text = """
        <p>How to use this tool:</p>

        <p>Annotation:</p>
        <ol>
        <li>Open Annotation tool by clicking the Open Annotation button on the left hand side pane.</li>
        <li>Open the video of your choice by navigating into the raw_video folder. This will automatically load up the associated CSV file.</li>
        <li>Set start and end point of the gesture.</li>
        <li>Enter a name for the gesture and click the Annotate button. This process will take some time as it is trimming the video and csv file to create a gesture entry.</li>
        <li>Make as many gesture entries as required and then close the tool.</li>
        </ol>

        <p>Visualization:</p>
        <ol>
        <li>Once you are done annotating your gestures open the visualization tool by clicking the Open Visualization tool on the left hand side pane.</li>
        <li>Select the filter that you want to apply to the data and set the desired weight that you want for that filter. Remember all the weights should add up to 1.</li>
        <li>Generate a heatmap plot to see how well your model performs. Play around with different values.</li>
        <li>Once you have found the best model, save it using the Save Model button.</li>
        <li>Close the tool after you are done generating models.</li>
        </ol>

        <p>Detection:</p>
        <ol>
        <li>Now that you have your own model, it is time to put it to test.</li>
        <li>Click the Open Detection button on the left hand side pane to open the detection tool.</li>
        <li>Choose your model from the dropdown list and open the video you want to apply the detection algorithm.</li>
        <li>See the performance of your model on real time.</li>
        </ol>
        """

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

            QLabel { 
                color: white; 
                background-color: #202124;
                text-indent: 0px;
                padding: 0px;
                margin-left: 10px; /* Adjust this value as needed */
            } 

            QScrollArea {
                background-color: #202124;
                border: 0px;
            }

            QStatusBar { 
                background-color: black; 
            }
            """
        )

        self.annotation_window = None
        self.visualization_window = None
        self.detection_window = None

        self.heading_label = QtWidgets.QLabel("AAC Data Analytics tool")
        self.heading_label.setStyleSheet("font-size: 70px; font-family: Roboto;")
        self.heading_label.setContentsMargins(0, 0, 0, 0)
        self.heading_label.setIndent(0)

        self.button_annotation = QtWidgets.QPushButton("Open Annotation", self)
        self.button_annotation.clicked.connect(self.open_annotation)

        self.button_visualization = QtWidgets.QPushButton("Open Visualiztion", self)
        self.button_visualization.clicked.connect(self.open_visualization)

        self.button_detection = QtWidgets.QPushButton("Open Detection", self)
        self.button_detection.clicked.connect(self.open_detection)

        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.addWidget(self.button_annotation)
        self.button_layout.addWidget(self.button_visualization)
        self.button_layout.addWidget(self.button_detection)

        self.howto_label = QtWidgets.QLabel(self.howtouse_text)
        self.howto_label.setTextFormat(QtCore.Qt.RichText)
        self.howto_label.setWordWrap(True)
        self.howto_label.setIndent(0)

        self.scroll_area = QtWidgets.QScrollArea()  # Create a QScrollArea
        self.scroll_area.setWidget(
            self.howto_label
        )  # Put the QLabel inside the QScrollArea
        self.scroll_area.setWidgetResizable(True)  # Make the QScrollArea resizable

        self.howto_layout = QtWidgets.QVBoxLayout()
        self.howto_layout.setContentsMargins(0, 0, 0, 0)
        self.howto_layout.addWidget(
            self.scroll_area
        )  # Add the QScrollArea to the layout instead of the QLabel

        self.layout_nothead = QtWidgets.QHBoxLayout()
        self.layout_nothead.addLayout(self.button_layout)
        self.layout_nothead.addLayout(self.howto_layout)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.heading_label)
        self.layout.addLayout(self.layout_nothead)

        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def open_annotation(self):
        if self.visualization_window is not None:
            self.visualization_window.close()
            self.visualization_window = None

        if self.detection_window is not None:
            self.detection_window.close()
            self.detection_window = None

        self.annotation_window = AnnotationWindow()
        self.annotation_window.show()

    def open_visualization(self):
        if self.annotation_window is not None:
            self.annotation_window.close()
            self.annotation_window = None

        if self.detection_window is not None:
            self.detection_window.close()
            self.detection_window = None

        self.visualization_window = VisualizationWindow()
        self.visualization_window.show()

    def open_detection(self):
        if self.annotation_window is not None:
            self.annotation_window.close()
            self.annotation_window = None

        if self.visualization_window is not None:
            self.visualization_window.close()
            self.visualization_window = None

        self.detection_window = DetectionWindow()
        self.detection_window.show()


if __name__ == "__main__":
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    app.exec_()
