"""
Specifies the abstract base class for resolving layer densities from formula strings.
"""

from abc import ABC, abstractmethod

from .chemical_formula import Formula


class MaterialResolver(ABC):
    comment = None  # comment can be set during a resolve to specify the origin of the data, it can also be constant

    def resolve_item(self, name) -> None | dict:
        """
        Optional method for resolving names directly ot Layer or SubStack
        compatible class.

        Returns such object or None if name cannot be resolved.
        """
        return None

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
