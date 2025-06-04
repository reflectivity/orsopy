"""
Build-in blocks of physical units used in model to describe more complex systems.

All these need to follow the .model_building_blocks.SubStackType protocol and
have a common "sub_stack_class" attribute that has to be set to the class name.
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Union

from .base import ComplexValue, Header, Value
from .model_building_blocks import SPECIAL_MATERIALS, Composit, Layer, Material, ModelParameters, SubStackType


@dataclass
class FunctionTwoElements(Header, SubStackType):
    material1: str
    material2: str
    function: str
    thickness: Optional[Union[float, Value]] = None
    roughness: Optional[Union[float, Value]] = None
    slice_resolution: Optional[Union[float, Value]] = None
    sub_stack_class: Literal["FunctionTwoElements"] = "FunctionTwoElements"

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
        if self.thickness is None:
            self.thickness = Value(0.0, unit=defaults.length_unit)
        elif not isinstance(self.thickness, Value):
            self.thickness = Value(self.thickness, unit=defaults.length_unit)
        elif self.thickness.unit is None:
            self.thickness.unit = defaults.length_unit

        if self.roughness is None:
            self.roughness = defaults.roughness
        elif not isinstance(self.roughness, Value):
            self.roughness = Value(self.roughness, unit=defaults.length_unit)
        elif self.roughness.unit is None:
            self.roughness.unit = defaults.length_unit

        if self.slice_resolution is None:
            self.slice_resolution = defaults.slice_resolution
        elif not isinstance(self.slice_resolution, Value):
            self.slice_resolution = Value(self.slice_resolution, unit=defaults.length_unit)
        elif self.slice_resolution.unit is None:
            self.slice_resolution.unit = defaults.length_unit

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
        # use the approximate slice resolution but make sure the total thickness is exact
        length_unit = self.thickness.unit
        slices = int(round(self.thickness.magnitude / self.slice_resolution.as_unit(length_unit)))
        di = self.thickness.magnitude / slices
        thickness = Value(magnitude=di, unit=length_unit)
        roughness = Value(magnitude=di / 2.0, unit=length_unit)
        output = []
        for i in range(slices):
            loc = {"x": (i + 0.5) / slices}
            fraction = max(0.0, min(1.0, eval(self.function, glo, loc)))
            composition = Composit(composition={self.material1: (1.0 - fraction), self.material2: fraction})
            composition.resolve_names({self.material1: self._materials[0], self.material2: self._materials[1]})
            output.append(Layer(material=composition, thickness=thickness, roughness=roughness))
        output[0].roughness = self.roughness
        return output
