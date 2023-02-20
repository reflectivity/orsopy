"""
Specifies the abstract base class for resolving layer densities from formula strings.
"""

from abc import ABC, abstractmethod

from .chemical_formula import Formula


class DensityResolver(ABC):
    comment = None  # comment can be set during a resolve to specify the origin of the data, it can also be constant

    @abstractmethod
    def resolve_formula(self, formula: Formula) -> float:
        """
        Resolves the density of a given chemical formula from the
        database. If not possible raises ValueError.

        The returned value is the number density in 1/nm³.
        """

    @abstractmethod
    def resolve_elemental(self, formula: Formula) -> float:
        """
        Estimates the density of a material from its individual elements
        by averaging the bulk element densities.

        The returned value is the number density in 1/nm³.
        """
