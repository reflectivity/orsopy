"""
Build-in blocks of physical units used in model to describe more complex systems.

All these need to follow the .model_building_blocks.SubStackType protocol.
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from .base import ComplexValue, Header, Value
from .model_building_blocks import SPECIAL_MATERIALS, SUBSTACK_TYPES, Composit, Layer, Material, ModelParameters


@dataclass
class FunctionTwoElements(Header):
    material1: str
    material2: str
    total_thickness: Union[float, Value]
    function: str
    slices: Optional[int] = 15

    def resolve_names(self, resolvable_items):
        self._materials = []
        for i, mi in enumerate([self.material1, self.material2]):
            if mi in resolvable_items:
                material = resolvable_items[mi]
            elif mi in SPECIAL_MATERIALS:
                material = SPECIAL_MATERIALS[mi]
            else:
                material = Material(formula=mi)
            self._materials.append(material)

    def resolve_defaults(self, defaults: ModelParameters) -> None:
        if not isinstance(self.total_thickness, Value):
            self.total_thickness = Value(self.total_thickness, unit=defaults.length_unit)

    def resolve_to_layers(self) -> List[Layer]:
        # pre-defined math functions allowed
        from math import acos, asin, atan, cos, exp, pi, sin, sqrt, tan

        loc = {}
        glo = {
            "sqrt": sqrt,
            "exp": exp,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "pi": pi,
            "arcsin": asin,
            "arccos": acos,
            "arctan": atan,
        }
        di = self.total_thickness.magnitude / self.slices
        thickness = Value(magnitude=di, unit=self.total_thickness.unit)
        output = []
        for i in range(self.slices):
            loc = {"x": (i + 0.5) / self.slices}
            fraction = max(0.0, min(1.0, eval(self.function, glo, loc)))
            composition = Composit(composition={self.material1: (1.0 - fraction), self.material2: fraction})
            composition.resolve_names({self.material1: self._materials[0], self.material2: self._materials[1]})
            output.append(Layer(material=composition, thickness=thickness))
        return output


SUBSTACK_TYPES.append(FunctionTwoElements)
