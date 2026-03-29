import PyQt5 as qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import numpy as np

#-- COLORS --#
background = '#2c2c2c'
#------------#

#-- MAIN WINDOW --#
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Window")
        self.setGeometry(200, 200, 400, 400)
        self.setStyleSheet(f"background-color: {background};")

        # Create a button to open the graph window
        self.open_graph_button = QPushButton("Open Graph Window", self)
        self.open_graph_button.clicked.connect(self.open_graph_window)

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.open_graph_button)

        container = qt.QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_graph_window(self):
        self.graph_window = GraphWindow()
        self.graph_window.show()

#-- GRAPH WINDOW --#
class GraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Graph Window")
        self.setGeometry(150, 150, 600, 400)
        self.setStyleSheet(f"background-color: {background};")

        # Create a button to start the graph animation
        self.start_animation_button = QPushButton("Start Graph Animation", self)
        self.start_animation_button.clicked.connect(self.start_graph_animation)

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.start_animation_button)

        container = qt.QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_graph_animation(self):
        fig, ax = plt.subplots()
        xdata, ydata = [], []
        ln, = plt.plot([], [], 'r-')

        def init():
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            return ln,

        def update(frame):
            xdata.append(frame)
            ydata.append(np.sin(frame))
            ln.set_data(xdata, ydata)
            return ln,

        ani = animation.FuncAnimation(fig, update, frames=np.linspace(0, 10, 100),
                                      init_func=init, blit=True)
        plt.show()

def graph_animation():
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'r-')

    def init():
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        return ln,

    def update(frame):
        xdata.append(frame)
        ydata.append(np.sin(frame))
        ln.set_data(xdata, ydata)
        return ln,

    ani = animation.FuncAnimation(fig, update, frames=np.linspace(0, 10, 100),
                                  init_func=init, blit=True)
    plt.show()



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()




