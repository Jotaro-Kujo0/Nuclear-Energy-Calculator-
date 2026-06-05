# Nuclear Energy Calculator

A calculatır/simulator I designed myself. utility designed to calculate energy output, mass defect, and efficiency for nuclear reactions. It simplifies complex physics equations into a clean, accessible interface for educational or hobbyist engineering use. still in development

---

## Main Goal

Simulating the energy released during nuclear fission and fusion by determining the difference between the starting mass of the reactants and the final mass of the products (the mass defect, $\Delta m$). 

Its using Einstein's mass-energy equivalence principle, the energy released ($E$) is calculated using the formula:

$$E = \Delta m \cdot c^2$$

Where:
* $E$ is the energy released (in Joules or Megaelectronvolts, MeV)
* $\Delta m$ is the mass defect (in kilograms or Atomic Mass Units, amu)
* $c$ is the speed of light in a vacuum ($2.998 \times 10^8 \text{ m/s}$)

---

## Key Features

* **Mass-Energy Conversion:** Calculate precise energy release based on mass defect.
* **Isotope Database Support:** Built-in values for standard nuclear fuels (e.g., Uranium-235, Deuterium-Tritium).
* **Efficiency Analysis:** Determine real-world power output based on thermal efficiency percentages.
* **Simple Interface:** Clean, focused console logic for quick, reproducible calculations. Its using common pyrhon textures at the moment, I will make custom ones.

---

## Getting Started

### Prerequisites
* Python 3.x Installed
* No external dependencies required (built using standard library modules)

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/Jotaro-Kujo0/Nuclear-Energy-Calculator-.git](https://github.com/Jotaro-Kujo0/Nuclear-Energy-Calculator-.git)
