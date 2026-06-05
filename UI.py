import sys
import random
import datetime
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QFormLayout, QComboBox, QFileDialog, QMessageBox, QSpinBox, QMainWindow
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from config import BACKGROUND_COLOR
from elementconfig import DEFAULT_LIBRARY, Isotope
from nuclear_energy_calculator import NuclearPhysics

class NuclearSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nuclear Simulator")
        self.resize(1400, 780)
        self.library = DEFAULT_LIBRARY.copy()
        self.run_counter = 0
        self.plotted_runs = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        form = QFormLayout()

        self.iso_combo = QComboBox()
        self._refresh_iso_combo()
        form.addRow("Isotope:", self.iso_combo)

        self.z_input = QSpinBox(); self.z_input.setRange(0, 300)
        self.a_input = QSpinBox(); self.a_input.setRange(1, 600)
        self.mass_input = QLineEdit()
        form.addRow("Protons (Z):", self.z_input)
        form.addRow("Nucleons (A):", self.a_input)
        form.addRow("Mass (u):", self.mass_input)

        self.temp_input = QLineEdit()
        self.rad_type = QComboBox(); self.rad_type.addItems(["Gamma", "Beta", "Alpha"])
        self.decay_mode = QComboBox(); self.decay_mode.addItems(["None", "Beta decay", "Gamma emission", "Fission-like split"])
        self.capture_type = QComboBox(); self.capture_type.addItems(["Simple atoms", "Complex atoms"])
        form.addRow("Temp (K):", self.temp_input)
        form.addRow("Radiation:", self.rad_type)
        form.addRow("Decay:", self.decay_mode)
        form.addRow("Net:", self.capture_type)

        left.addLayout(form)

        btn_row = QHBoxLayout()
        calc_btn = QPushButton("Calculate Physics"); calc_btn.clicked.connect(self._do_calc)
        add_btn = QPushButton("Update Library"); add_btn.clicked.connect(self._add_update_isotope)
        btn_row.addWidget(calc_btn); btn_row.addWidget(add_btn)
        left.addLayout(btn_row)

        self.queue_list = QListWidget()
        left.addWidget(QLabel("Reaction Queue"))
        left.addWidget(self.queue_list)

        qbtn_row = QHBoxLayout()
        q_sel = QPushButton("Queue Selected"); q_sel.clicked.connect(self._queue_selected)
        q_clr = QPushButton("Clear Queue"); q_clr.clicked.connect(lambda: self.queue_list.clear())
        qbtn_row.addWidget(q_sel); qbtn_row.addWidget(q_clr)
        left.addLayout(qbtn_row)

        run_btn = QPushButton("Run Simulation"); run_btn.clicked.connect(self._run_simulation)
        left.addWidget(run_btn)

        self.terminal = QTextEdit(); self.terminal.setReadOnly(True)
        layout.addLayout(left, 3)

        center = QVBoxLayout()
        self.canvas = FigureCanvas(Figure())
        self.ax = self.canvas.figure.subplots()
        center.addWidget(self.canvas)
        center.addWidget(self.terminal)
        layout.addLayout(center, 6)

        right = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Z", "A", "Mass"])
        right.addWidget(self.table)
        layout.addLayout(right, 3)

        self._refresh_table()
        self.iso_combo.currentIndexChanged.connect(self._on_iso_selected)

    def log(self, text):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.append(f"[{ts}] {text}")

    def _refresh_iso_combo(self):
        self.iso_combo.clear()
        self.iso_combo.addItems([i.name for i in self.library])

    def _refresh_table(self):
        self.table.setRowCount(len(self.library))
        for i, iso in enumerate(self.library):
            self.table.setItem(i, 0, QTableWidgetItem(iso.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(iso.Z)))
            self.table.setItem(i, 2, QTableWidgetItem(str(iso.A)))
            self.table.setItem(i, 3, QTableWidgetItem(str(iso.atomic_mass_u)))

    def _on_iso_selected(self, idx):
        if 0 <= idx < len(self.library):
            iso = self.library[idx]
            self.z_input.setValue(iso.Z)
            self.a_input.setValue(iso.A)
            self.mass_input.setText(str(iso.atomic_mass_u))

    def _add_update_isotope(self):
        Z, A = self.z_input.value(), self.a_input.value()
        m = float(self.mass_input.text())
        name = f"X-{A}"
        for iso in self.library:
            if iso.Z == Z and iso.A == A:
                iso.atomic_mass_u, iso.name = m, name
                break
        else:
            self.library.append(Isotope(name, Z, A, m))
        self._refresh_iso_combo(); self._refresh_table()

    def _do_calc(self):
        iso = self.library[self.iso_combo.currentIndex()]
        b, per = NuclearPhysics.binding_energy(iso.Z, iso.A, iso.atomic_mass_u)
        f = NuclearPhysics.photon_freq(b)
        self.log(f"{iso.name}: B={b:.4f}MeV, B/A={per:.4f}MeV, f={f:.2e}Hz")

    def _queue_selected(self):
        self.queue_list.addItem(self.iso_combo.currentText())

    def _run_simulation(self):
        if not self.queue_list.count(): return
        temp = float(self.temp_input.text() or 0)
        eff = min(1.0, max(0.0, 1.0 - (temp/1000.0)))
        
        steps, released, captured = [], [], []
        while self.queue_list.count():
            name = self.queue_list.takeItem(0).text()
            iso = next(i for i in self.library if i.name == name)
            b, _ = NuclearPhysics.binding_energy(iso.Z, iso.A, iso.atomic_mass_u)
            
            r_val = b * (1.25 if self.decay_mode.currentText() == "Fission-like split" else 1.0)
            c_val = r_val * eff
            
            steps.append(len(steps)+1)
            released.append(r_val)
            captured.append(c_val)
            self.log(f"Step {steps[-1]}: {name} -> R:{r_val:.2f} C:{c_val:.2f}")

        self.ax.plot(steps, released, 'r-', label="Released")
        self.ax.plot(steps, captured, 'b--', label="Captured")
        self.ax.legend()
        self.canvas.draw()