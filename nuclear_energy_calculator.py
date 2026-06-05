import math
from config import C, U_TO_KG, J_TO_MEV, MEV_TO_J, H_PLANCK, M_H_ATOM_U, M_N_U

class NuclearPhysics:
    @staticmethod
    def energy_from_u(mass_u):
        return (mass_u * U_TO_KG * C**2) * J_TO_MEV

    @staticmethod
    def binding_energy(Z, A, atomic_mass_u):
        mass_sum_u = Z * M_H_ATOM_U + (A - Z) * M_N_U
        delta_u = mass_sum_u - atomic_mass_u
        B_MeV = NuclearPhysics.energy_from_u(delta_u)
        return B_MeV, (B_MeV / A if A > 0 else 0.0)

    @staticmethod
    def photon_freq(E_MeV):
        return (E_MeV * MEV_TO_J) / H_PLANCK

    @staticmethod
    def doppler_shift(f, v):
        return f * (1.0 + v / C)

    @staticmethod
    def beta_minus_q(parent_u, daughter_u):
        return NuclearPhysics.energy_from_u(parent_u - daughter_u)