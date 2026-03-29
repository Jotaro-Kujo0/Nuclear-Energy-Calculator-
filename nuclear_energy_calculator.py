#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Simple nuclear calculator: mass-energy, binding energy, beta-minus Q, gamma frequency, Doppler

c = 299_792_458.0
u_to_kg = 1.660_539_066_60e-27
MeV_to_J = 1.602_176_634e-13
J_to_MeV = 1.0 / MeV_to_J
h = 6.626_070_15e-34
m_H_atom_u = 1.007_825_032_23
m_n_u = 1.008_664_915_88

def mass_energy_equivalence_from_u(mass_u: float):
    mass_kg = mass_u * u_to_kg
    E_J = mass_kg * c**2
    E_MeV = E_J * J_to_MeV
    return {"mass_u": mass_u, "mass_kg": mass_kg, "E_J": E_J, "E_MeV": E_MeV}

def binding_energy_from_atomic_mass(Z: int, A: int, atomic_mass_u: float):
    mass_sum_u = Z * m_H_atom_u + (A - Z) * m_n_u
    delta_u = mass_sum_u - atomic_mass_u
    E = mass_energy_equivalence_from_u(delta_u)
    B_MeV = E["E_MeV"]
    return B_MeV, (B_MeV / A if A>0 else float("nan")), delta_u

def beta_minus_Q_value(parent_atom_mass_u: float, daughter_atom_mass_u: float):
    delta_u = parent_atom_mass_u - daughter_atom_mass_u
    return mass_energy_equivalence_from_u(delta_u)["E_MeV"]

def photon_frequency_from_energy_MeV(E_MeV: float):
    return (E_MeV * MeV_to_J) / h

def doppler_shifted_frequency(f: float, v: float):
    return f * (1.0 + v / c)

if __name__ == "__main__":
    Z, A, m_atom_u = 1, 2, 2.014_101_778_12  # D-2 example
    B, B_A, du = binding_energy_from_atomic_mass(Z, A, m_atom_u)
    f_gamma = photon_frequency_from_energy_MeV(B)
    print("Deuterium binding (MeV):", B, "B/A:", B_A, "mass defect (u):", du)
    print("Gamma-equiv freq (Hz):", f_gamma)
