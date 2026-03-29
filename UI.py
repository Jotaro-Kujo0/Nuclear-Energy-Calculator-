#!/usr/bin/env python3
"""
nuclear_simulator_full.py

Comprehensive desktop simulator combining:
- isotope library and editing
- physics helpers (binding energy, mass-energy, gamma freq, Doppler)
- scenario controls (temp, radiation type, decay, capture net)
- reaction queue and simulation engine
- interactive command console
- Matplotlib plotting of multiple runs (colored lines)
- export plot and log

Dependencies:
    pip install pyqt5 matplotlib

Run:
    python nuclear_simulator_full.py
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict
import math
import random
import sys
import datetime

# GUI & plotting
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QFormLayout, QComboBox, QFileDialog, QMessageBox, QSpinBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ---------------- Physics constants & helpers ----------------
c = 299_792_458.0                      # speed of light m/s
u_to_kg = 1.66053906660e-27           # atomic mass unit to kg
MeV_to_J = 1.602176634e-13
J_to_MeV = 1.0 / MeV_to_J
h = 6.62607015e-34                    # Planck constant J*s
m_H_atom_u = 1.00782503223            # H-1 atomic mass (includes electron)
m_n_u = 1.00866491588                 # neutron mass (u)

def mass_energy_equivalence_from_u(mass_u: float) -> float:
    """Return energy in MeV for mass in atomic mass units (u)."""
    mass_kg = mass_u * u_to_kg
    E_J = mass_kg * c**2
    return E_J * J_to_MeV

def binding_energy_from_atomic_mass(Z:int, A:int, atomic_mass_u:float) -> Tuple[float,float]:
    """
    Compute binding energy (MeV) using atomic masses (electrons included so cancellation is OK).
    Returns (total_B_MeV, per_nucleon_MeV).
    """
    mass_sum_u = Z * m_H_atom_u + (A - Z) * m_n_u
    delta_u = mass_sum_u - atomic_mass_u
    B_MeV = mass_energy_equivalence_from_u(delta_u)
    per = (B_MeV / A) if A > 0 else 0.0
    return B_MeV, per

def photon_frequency_from_energy_MeV(E_MeV: float) -> float:
    """Return photon frequency in Hz for energy in MeV (E = h f)."""
    E_J = E_MeV * MeV_to_J
    return E_J / h

def doppler_shift_nonrel(f: float, v: float) -> float:
    """Non-relativistic Doppler shift (approx) for target velocity v (m/s)."""
    return f * (1.0 + v / c)

def beta_minus_Q_value(parent_mass_u: float, daughter_mass_u: float) -> float:
    """Q-value (MeV) for beta-minus decay given atomic masses (parents - daughter)."""
    delta_u = parent_mass_u - daughter_mass_u
    return mass_energy_equivalence_from_u(delta_u)

# ---------------- Data classes ----------------
@dataclass
class Isotope:
    name: str
    Z: int
    A: int
    atomic_mass_u: float

# Default library
DEFAULT_LIBRARY: List[Isotope] = [
    Isotope("H-1", 1, 1, 1.00782503223),
    Isotope("D-2", 1, 2, 2.01410177812),
    Isotope("T-3", 1, 3, 3.01604928199),
    Isotope("He-3", 2, 3, 3.01602932265),
    Isotope("He-4", 2, 4, 4.00260325413),
    Isotope("Li-6", 3, 6, 6.0151228874),
    Isotope("Li-7", 3, 7, 7.0160034366),
    Isotope("Fe-56",26,56,55.9349375),
]

# ---------------- Simulator UI ----------------
class NuclearSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nuclear Simulator — Full")
        self.resize(1400, 780)
        self.library: List[Isotope] = DEFAULT_LIBRARY.copy()
        self.run_counter = 0
        self.plotted_runs: Dict[str, Dict] = {}  # store data for multiple runs
        self._last_saved_plot = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Left panel: controls, inputs, scenarios
        left = QVBoxLayout()
        form = QFormLayout()

        # isotope combobox
        self.iso_combo = QComboBox()
        self._refresh_iso_combo()
        form.addRow(QLabel("Choose Isotope:"), self.iso_combo)

        # isotope inputs
        self.z_input = QSpinBox(); self.z_input.setRange(0,300)
        self.a_input = QSpinBox(); self.a_input.setRange(1,600)
        self.mass_input = QLineEdit()
        form.addRow(QLabel("Protons (Z):"), self.z_input)
        form.addRow(QLabel("Nucleons (A):"), self.a_input)
        form.addRow(QLabel("Atomic mass (u):"), self.mass_input)

        # scenario controls
        self.temp_input = QLineEdit(); self.temp_input.setPlaceholderText("Temperature in K (0 recommended for best capture)")
        self.rad_type = QComboBox(); self.rad_type.addItems(["Gamma","Beta","Alpha"])
        self.decay_mode = QComboBox(); self.decay_mode.addItems(["None","Beta decay","Gamma emission","Fission-like split"])
        self.capture_type = QComboBox(); self.capture_type.addItems(["Simple atoms","Complex atoms"])
        form.addRow(QLabel("Temperature (K):"), self.temp_input)
        form.addRow(QLabel("Radiation type:"), self.rad_type)
        form.addRow(QLabel("Decay mode:"), self.decay_mode)
        form.addRow(QLabel("Capture net type:"), self.capture_type)

        left.addLayout(form)

        # action buttons
        btn_row = QHBoxLayout()
        calc_btn = QPushButton("Calc Binding & Photon Freq"); calc_btn.clicked.connect(self._do_calc)
        add_btn = QPushButton("Add/Update Isotope"); add_btn.clicked.connect(self._add_update_isotope)
        btn_row.addWidget(calc_btn); btn_row.addWidget(add_btn)
        left.addLayout(btn_row)

        # Reaction queue
        left.addWidget(QLabel("Reaction Queue (destroy items)"))
        self.queue_list = QListWidget()
        left.addWidget(self.queue_list)
        qbtn_row = QHBoxLayout()
        queue_selected = QPushButton("Queue Selected"); queue_selected.clicked.connect(self._queue_selected)
        queue_text = QPushButton("Queue by Name"); queue_text.clicked.connect(self._queue_by_name_dialog)
        qbtn_row.addWidget(queue_selected); qbtn_row.addWidget(queue_text)
        left.addLayout(qbtn_row)

        # Simulation controls
        run_btn = QPushButton("Run Simulation"); run_btn.clicked.connect(self._run_simulation)
        left.addWidget(run_btn)

        # command console
        left.addWidget(QLabel("Command Console"))
        self.command_input = QLineEdit(); self.command_input.setPlaceholderText("e.g. queue H-1 | set temp 50 | run | plot save.png")
        run_cmd = QPushButton("Execute Command"); run_cmd.clicked.connect(self._execute_command)
        left.addWidget(self.command_input); left.addWidget(run_cmd)

        # quick actions
        left.addWidget(QLabel("Quick actions"))
        quick_row = QHBoxLayout()
        clear_queue_btn = QPushButton("Clear Queue"); clear_queue_btn.clicked.connect(lambda: self.queue_list.clear())
        clear_plot_btn = QPushButton("Clear Plot"); clear_plot_btn.clicked.connect(self._clear_plot)
        quick_row.addWidget(clear_queue_btn); quick_row.addWidget(clear_plot_btn)
        left.addLayout(quick_row)

        # export & save
        save_plot_btn = QPushButton("Save Plot & Log"); save_plot_btn.clicked.connect(self._save_plot_and_log)
        left.addWidget(save_plot_btn)

        layout.addLayout(left, 3)

        # Center panel: plot and log
        center = QVBoxLayout()
        self.canvas = FigureCanvas(Figure(figsize=(6.5,5)))
        self.ax = self.canvas.figure.subplots()
        center.addWidget(self.canvas)

        # run list -> keep run names & toggle show/hide
        run_controls = QHBoxLayout()
        self.run_name_input = QLineEdit(); self.run_name_input.setPlaceholderText("Optional run name")
        show_runs_btn = QPushButton("List Runs"); show_runs_btn.clicked.connect(self._list_runs)
        run_controls.addWidget(self.run_name_input); run_controls.addWidget(show_runs_btn)
        center.addLayout(run_controls)

        center.addWidget(QLabel("Terminal / Log"))
        self.terminal = QTextEdit(); self.terminal.setReadOnly(True)
        center.addWidget(self.terminal)
        layout.addLayout(center, 6)

        # Right panel: isotope table & info
        right = QVBoxLayout()
        right.addWidget(QLabel("Isotope Library"))
        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Name","Z","A","Mass (u)"])
        right.addWidget(self.table)

        # info buttons
        info_row = QHBoxLayout()
        detail_btn = QPushButton("Show Selected Info"); detail_btn.clicked.connect(self._show_selected_info)
        remove_btn = QPushButton("Remove Selected"); remove_btn.clicked.connect(self._remove_selected)
        info_row.addWidget(detail_btn); info_row.addWidget(remove_btn)
        right.addLayout(info_row)

        layout.addLayout(right, 3)

        # initialize table & combobox selection handler
        self._refresh_table()
        self.iso_combo.currentIndexChanged.connect(self._on_iso_selected)
        if self.library:
            self._on_iso_selected(0)

    # ---------------- UI helper methods ----------------
    def log(self, text: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.append(f"[{now}] {text}")

    def _refresh_iso_combo(self):
        self.iso_combo.clear()
        for iso in self.library:
            self.iso_combo.addItem(iso.name)

    def _refresh_table(self):
        self.table.setRowCount(len(self.library))
        for i,iso in enumerate(self.library):
            self.table.setItem(i,0,QTableWidgetItem(iso.name))
            self.table.setItem(i,1,QTableWidgetItem(str(iso.Z)))
            self.table.setItem(i,2,QTableWidgetItem(str(iso.A)))
            self.table.setItem(i,3,QTableWidgetItem(str(iso.atomic_mass_u)))
        self.table.resizeColumnsToContents()

    # ---------------- Isotope handlers ----------------
    def _on_iso_selected(self, idx:int):
        if idx < 0 or idx >= len(self.library):
            return
        iso = self.library[idx]
        # set numeric spinboxes and mass text
        self.z_input.setValue(iso.Z)
        self.a_input.setValue(iso.A)
        self.mass_input.setText(str(iso.atomic_mass_u))

    def _add_update_isotope(self):
        try:
            Z = int(self.z_input.value())
            A = int(self.a_input.value())
            mass_u = float(self.mass_input.text())
            # name guess: element placeholder X-A unless matching known
            name = f"X-{A}"
            # If selection exists with same Z,A we update; otherwise append
            found = None
            for iso in self.library:
                if iso.Z == Z and iso.A == A:
                    found = iso; break
            if found:
                found.atomic_mass_u = mass_u
                found.name = name
                self.log(f"Updated isotope {found.name} Z={Z} A={A} mass={mass_u} u")
            else:
                new_iso = Isotope(name, Z, A, mass_u)
                self.library.append(new_iso)
                self.log(f"Added isotope {name} Z={Z} A={A} mass={mass_u} u")
            self._refresh_iso_combo(); self._refresh_table()
        except Exception as ex:
            QMessageBox.warning(self, "Input error", f"Invalid input: {ex}")

    def _remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            self.log("No isotope row selected for removal.")
            return
        name = self.table.item(row,0).text()
        self.library = [iso for iso in self.library if iso.name != name]
        self._refresh_table(); self._refresh_iso_combo()
        self.log(f"Removed isotope {name}")

    def _show_selected_info(self):
        row = self.table.currentRow()
        if row < 0:
            self.log("No isotope selected.")
            return
        name = self.table.item(row,0).text()
        iso = next((x for x in self.library if x.name == name), None)
        if not iso:
            self.log("Selected isotope not found.")
            return
        B, per = binding_energy_from_atomic_mass(iso.Z, iso.A, iso.atomic_mass_u)
        freq = photon_frequency_from_energy_MeV(B)
        self.log(f"Isotope {iso.name}: Z={iso.Z}, A={iso.A}, mass={iso.atomic_mass_u} u | Binding={B:.6f} MeV ({per:.6f} MeV/nucleon) | gamma-freq ≈ {freq:.3e} Hz")

    # ---------------- Queue operations ----------------
    def _queue_selected(self):
        name = self.iso_combo.currentText()
        if not name:
            self.log("No isotope selected to queue.")
            return
        self.queue_list.addItem(f"Destroy {name}")
        self.log(f"Queued: Destroy {name}")

    def _queue_by_name_dialog(self):
        text, ok = QFileDialog.getOpenFileName(self, "Select text file containing isotope names (one per line)", "", "Text Files (*.txt);;All Files (*)")
        if ok and text:
            try:
                with open(text, 'r', encoding='utf-8') as f:
                    for line in f:
                        nm = line.strip()
                        if not nm: continue
                        # accept either literal name or X-A; verify existence
                        iso = next((x for x in self.library if x.name.lower() == nm.lower()), None)
                        if iso:
                            self.queue_list.addItem(f"Destroy {iso.name}")
                            self.log(f"Queued (file): {iso.name}")
                        else:
                            self.log(f"Name from file not found in library: {nm}")
            except Exception as e:
                self.log(f"Error reading file: {e}")

    # ---------------- Simulation core ----------------
    def _run_simulation(self):
        if self.queue_list.count() == 0:
            self.log("Queue empty — nothing to run.")
            return

        # read scenario
        try:
            temp = float(self.temp_input.text() or 0.0)
        except:
            temp = 0.0
        rad = self.rad_type.currentText()
        decay = self.decay_mode.currentText()
        capture_net = self.capture_type.currentText()

        # compute capture efficiency (toy model)
        # colder -> better capture; complex nets slightly better
        base_eff = max(0.0, 1.0 - (temp / 1000.0))  # 0K -> 1.0, 1000K -> 0.0
        if capture_net == "Complex atoms":
            base_eff *= 1.1
        base_eff = min(base_eff, 1.0)

        # Setup run name
        run_name = self.run_name_input.text().strip() or f"run_{self.run_counter+1}"
        self.run_counter += 1
        color_released = self._rand_color()
        color_captured = self._rand_color()

        steps = []
        released = []
        captured = []
        step_index = 0
        self.log(f"\n--- Simulation START: {run_name} (T={temp}K, rad={rad}, decay={decay}, net={capture_net}) ---")

        # drain queue
        while self.queue_list.count() > 0:
            item = self.queue_list.takeItem(0)
            text = item.text().strip()
            if not text:
                continue
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                continue
            name = parts[1]
            iso = next((x for x in self.library if x.name == name), None)
            if iso is None:
                self.log(f"Isotope {name} not found — skipped.")
                continue

            step_index += 1
            # binding energy approximate:
            B_total, B_per = binding_energy_from_atomic_mass(iso.Z, iso.A, iso.atomic_mass_u)
            energy_released = B_total  # baseline

            # apply decay/rad toy modifiers
            if decay == "Beta decay":
                energy_released *= 0.92
            elif decay == "Gamma emission":
                energy_released *= 1.00
            elif decay == "Fission-like split":
                energy_released *= 1.25

            if rad == "Alpha":
                energy_released *= 0.97
            elif rad == "Beta":
                energy_released *= 0.99
            elif rad == "Gamma":
                energy_released *= 1.02

            # energy captured by net:
            energy_caught = energy_released * base_eff

            steps.append(step_index)
            released.append(energy_released)
            captured.append(energy_caught)

            self.log(f"Step {step_index}: Destroy {iso.name} -> Released {energy_released:.6f} MeV | Captured {energy_caught:.6f} MeV")

        # plot the run as two lines (released & captured)
        if steps:
            ax = self.ax
            ax.plot(steps, released, marker='o', linestyle='-', color=color_released, label=f"{run_name} - released")
            ax.plot(steps, captured, marker='o', linestyle='--', color=color_captured, label=f"{run_name} - captured")
            ax.set_xlabel("Reaction step")
            ax.set_ylabel("Energy (MeV)")
            ax.set_title("Simulation runs (multiple runs overlay)")
            ax.legend(loc='upper right', fontsize='small')
            self.canvas.draw()
            # store run for later listing
            self.plotted_runs[run_name] = {
                "steps": steps.copy(),
                "released": released.copy(),
                "captured": captured.copy(),
                "meta": {"temp": temp, "rad": rad, "decay": decay, "net": capture_net},
                "colors": {"released": color_released, "captured": color_captured},
            }
            self.log(f"--- Simulation COMPLETE: {run_name} (plotted) ---")
        else:
            self.log("No valid steps were processed in the simulation.")

    # ---------------- Command console ----------------
    def _execute_command(self):
        cmd = self.command_input.text().strip()
        if not cmd:
            return
        self.log(f"> {cmd}")
        lc = cmd.lower()
        if lc.startswith("queue "):
            name = cmd[6:].strip()
            iso = next((x for x in self.library if x.name.lower() == name.lower()), None)
            if iso:
                self.queue_list.addItem(f"Destroy {iso.name}")
                self.log(f"Cmd: queued {iso.name}")
            else:
                self.log(f"Cmd: isotope '{name}' not found")
        elif lc.startswith("set temp "):
            try:
                val = float(cmd.split()[2])
                self.temp_input.setText(str(val))
                self.log(f"Cmd: temperature set to {val} K")
            except:
                self.log("Cmd: invalid set temp syntax, use: set temp 50")
        elif lc == "run":
            self._run_simulation()
        elif lc.startswith("plot save "):
            # plot save <path>
            try:
                path = cmd.split(" ", 2)[2]
                self.canvas.figure.savefig(path)
                self.log(f"Cmd: plot saved to {path}")
            except Exception as e:
                self.log(f"Cmd: error saving plot: {e}")
        elif lc == "clear":
            self.queue_list.clear()
            self.log("Cmd: cleared queue")
        elif lc == "plot clear":
            self._clear_plot()
        elif lc == "list runs":
            self._list_runs()
        else:
            self.log("Cmd: unknown. Use: queue <iso>, set temp <K>, run, plot save <path>, clear, plot clear, list runs")
        self.command_input.clear()

    # ---------------- Plot / export helpers ----------------
    def _clear_plot(self):
        self.ax.cla()
        self.canvas.draw()
        self.log("Plot cleared")

    def _list_runs(self):
        if not self.plotted_runs:
            self.log("No runs plotted yet.")
            return
        self.log("Plotted runs:")
        for name, data in self.plotted_runs.items():
            meta = data["meta"]
            self.log(f" - {name}: steps={len(data['steps'])} meta={meta}")

    def _save_plot_and_log(self):
        # save plot
        pth, _ = QFileDialog.getSaveFileName(self, "Save plot image", "", "PNG Files (*.png);;All files (*)")
        if pth:
            try:
                self.canvas.figure.savefig(pth)
                self._last_saved_plot = pth
                self.log(f"Plot saved to {pth}")
            except Exception as e:
                self.log(f"Error saving plot: {e}")
        # save log
        pth2, _ = QFileDialog.getSaveFileName(self, "Save log text", "", "Text Files (*.txt);;All files (*)")
        if pth2:
            try:
                with open(pth2, "w", encoding="utf-8") as f:
                    f.write(self.terminal.toPlainText())
                self.log(f"Log saved to {pth2}")
            except Exception as e:
                self.log(f"Error saving log: {e}")

    # ---------------- Misc helpers ----------------
    def _do_calc(self):
        # show binding, photon freq, doppler example for selected isotope
        name = self.iso_combo.currentText()
        iso = next((x for x in self.library if x.name == name), None)
        if not iso:
            self.log("No isotope chosen for calc.")
            return
        B, per = binding_energy_from_atomic_mass(iso.Z, iso.A, iso.atomic_mass_u)
        freq = photon_frequency_from_energy_MeV(B)
        # show a small doppler example for v = 1 m/s and v = 1000 m/s
        f_v1 = doppler_shift_nonrel(freq, 1.0)
        f_v1000 = doppler_shift_nonrel(freq, 1000.0)
        self.log(f"Calc {iso.name}: Binding={B:.6f} MeV ({per:.6f} MeV/nuc) | γ-freq={freq:.3e} Hz | f@1m/s={f_v1:.3e} Hz | f@1000m/s={f_v1000:.3e} Hz")

    def _rand_color(self) -> str:
        # return a visually distinct color
        return f"#{random.randint(0x20,0xD0):02x}{random.randint(0x20,0xD0):02x}{random.randint(0x20,0xD0):02x}"

# ---------------- Run the app ----------------
def main():
    app = QApplication(sys.argv)
    win = NuclearSimulator()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

