from dataclasses import dataclass

@dataclass
class Isotope:
    name: str
    Z: int
    A: int
    atomic_mass_u: float

DEFAULT_LIBRARY = [
    Isotope("H-1", 1, 1, 1.00782503223),
    Isotope("D-2", 1, 2, 2.01410177812),
    Isotope("T-3", 1, 3, 3.01604928199),
    Isotope("He-3", 2, 3, 3.01602932265),
    Isotope("He-4", 2, 4, 4.00260325413),
    Isotope("Li-6", 3, 6, 6.0151228874),
    Isotope("Li-7", 3, 7, 7.0160034366),
    Isotope("Fe-56", 26, 56, 55.9349375),
]