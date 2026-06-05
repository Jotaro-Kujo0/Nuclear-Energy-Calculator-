import sys
from PyQt5.QtWidgets import QApplication
from UI import NuclearSimulator

def main():
    app = QApplication(sys.argv)
    sim = NuclearSimulator()
    sim.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()