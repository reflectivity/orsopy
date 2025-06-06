"""
Build-in blocks of physical units used in model to describe more complex systems.

All these need to follow the .model_building_blocks.SubStackType protocol and
have a common "sub_stack_class" attribute that has to be set to the class name.
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from .base import ComplexValue, Header, Literal, Value
from .model_building_blocks import SPECIAL_MATERIALS, Composit, Layer, Material, ModelParameters, SubStackType


@dataclass
class FunctionTwoElements(Header, SubStackType):
    """
    Models a continous variation between two materials/SLDs according to an analytical function.

    The profile rho(z) is defined according to the relative layer thickness as fraction of material 2:
        rho(z) = (1-f((x-x0)/thickness))*rho_1 + f((x-x0)/thickness)*rho_2

    f is bracketed between 0 and 1 to prevent any artefacts with SLDs that are non-physical.

    The function string is evaluated according to python syntax using only build-in operators
    and a limited set of mathematical functions and constants defined in the class constant **ALLOWED_FUNCTIONS**.
    """

    material1: str
    material2: str
    function: str
    thickness: Optional[Union[float, Value]] = None
    roughness: Optional[Union[float, Value]] = None
    slice_resolution: Optional[Union[float, Value]] = None
    sub_stack_class: Literal["FunctionTwoElements"] = "FunctionTwoElements"

    ALLOWED_FUNCTIONS = [
        "pi",
        "sqrt",
        "exp",
        "sin",
        "cos",
        "tan",
        "sinh",
        "cosh",
        "tanh",
        "asin",
        "acos",
        "atan",
    ]

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
        glo = {}
        import math

        for name in self.ALLOWED_FUNCTIONS:
            param = getattr(math, name)
            glo[name] = param

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


@dataclass
class LipidLeaflet(Header, SubStackType):
    """
    Bilayer based on refnx.reflect.LipidLeaflet
    To keep consistent with other sample model elements, the thickness of tails is deduced from
    total thickness and thickness_heads.

    TODO: Review class parameters within ORSO.
    """

    apm: Union[float, Value]
    b_heads: Union[float, ComplexValue]
    vm_heads: Union[float, Value]
    b_tails: Union[float, ComplexValue]
    vm_tails: Union[float, Value]
    thickness_heads: Union[float, Value]
    roughness_head_tail: Optional[Union[float, Value]] = None
    head_solvent: Optional[Union[Material, Composit, str]] = None
    tail_solvent: Optional[Union[Material, Composit, str]] = None
    thickness: Optional[Union[float, Value]] = None
    roughness: Optional[Union[float, Value]] = None
    reverse_monolayer: bool = False

    sub_stack_class: Literal["LipidLeaflet"] = "LipidLeaflet"

    def resolve_names(self, resolvable_items):
        if isinstance(self.head_solvent, (Material, Composit)):
            pass
        elif self.head_solvent is None:
            if "environment" in resolvable_items:
                self.head_solvent = resolvable_items["environment"]
        elif self.head_solvent in resolvable_items:
            self.head_solvent = resolvable_items[self.head_solvent]
        elif self.head_solvent in SPECIAL_MATERIALS:
            self.head_solvent = SPECIAL_MATERIALS[self.head_solvent]
        else:
            self.head_solvent = Material(formula=self.head_solvent)

        if isinstance(self.tail_solvent, (Material, Composit)):
            pass
        elif self.tail_solvent is None:
            if "environment" in resolvable_items:
                self.tail_solvent = resolvable_items["environment"]
        elif self.tail_solvent in resolvable_items:
            self.tail_solvent = resolvable_items[self.tail_solvent]
        elif self.tail_solvent in SPECIAL_MATERIALS:
            self.tail_solvent = SPECIAL_MATERIALS[self.tail_solvent]
        else:
            self.tail_solvent = Material(formula=self.tail_solvent)

    def resolve_defaults(self, defaults: "ModelParameters"):
        if self.thickness is None:
            self.thickness = Value(0.0, unit=defaults.length_unit)
        elif not isinstance(self.thickness, Value):
            self.thickness = Value(self.thickness, unit=defaults.length_unit)
        elif self.thickness.unit is None:
            self.thickness.unit = defaults.length_unit

        if not isinstance(self.thickness_heads, Value):
            self.thickness_heads = Value(self.thickness_heads, unit=defaults.length_unit)
        elif self.thickness_heads.unit is None:
            self.thickness_heads.unit = defaults.length_unit

        if self.roughness is None:
            self.roughness = defaults.roughness
        elif not isinstance(self.roughness, Value):
            self.roughness = Value(self.roughness, unit=defaults.length_unit)
        elif self.roughness.unit is None:
            self.roughness.unit = defaults.length_unit

        if self.roughness_head_tail is None:
            self.roughness_head_tail = defaults.roughness
        elif not isinstance(self.roughness_head_tail, Value):
            self.roughness_head_tail = Value(self.roughness_head_tail, unit=defaults.length_unit)
        elif self.roughness_head_tail.unit is None:
            self.roughness_head_tail.unit = defaults.length_unit

        if not isinstance(self.b_heads, ComplexValue):
            self.b_heads = ComplexValue(real=self.b_heads, imag=0.0, unit=defaults.length_unit)
        if not isinstance(self.b_tails, ComplexValue):
            self.b_tails = ComplexValue(real=self.b_tails, imag=0.0, unit=defaults.length_unit)

        if not isinstance(self.apm, Value):
            self.apm = Value(self.apm, unit=defaults.length_unit + "^2")
        elif self.apm.unit is None:
            self.apm.unit = defaults.length_unit + "^2"

        if not isinstance(self.vm_heads, Value):
            self.vm_heads = Value(self.vm_heads, unit=defaults.length_unit + "^3")
        elif self.vm_heads.unit is None:
            self.vm_heads.unit = defaults.length_unit + "^3"

        if not isinstance(self.vm_tails, Value):
            self.vm_tails = Value(self.vm_tails, unit=defaults.length_unit + "^3")
        elif self.vm_tails.unit is None:
            self.vm_tails.unit = defaults.length_unit + "^3"

        if self.head_solvent is None:
            self.head_solvent = defaults.default_solvent
        if self.tail_solvent is None:
            self.tail_solvent = defaults.default_solvent

    @property
    def volfrac_h(self):
        # Volume fraction of head group in head group region
        return self.vm_heads.as_unit("Angstrom^3") / (
            self.apm.as_unit("Angstrom^2") * self.thickness_heads.as_unit("Angstrom")
        )

    @property
    def volfrac_t(self):
        # Volume fraction of head group in head group region
        return self.vm_tails.as_unit("Angstrom^3") / (
            self.apm.as_unit("Angstrom^2")
            * (self.thickness.as_unit("Angstrom") - self.thickness_heads.as_unit("Angstrom"))
        )

    def resolve_to_layers(self) -> List["Layer"]:
        sld_value = self.b_heads.as_unit("Angstrom") / self.vm_heads.as_unit("Angstrom^3")
        sld = ComplexValue(real=sld_value.real, imag=sld_value.imag, unit="1/Angstrom^2")
        composition_heads = Composit(composition={"sld_heads": self.volfrac_h, "solvent_heads": 1.0 - self.volfrac_h})
        composition_heads.resolve_names({"sld_heads": Material(sld=sld), "solvent_heads": self.head_solvent})
        heads = Layer(material=composition_heads, thickness=self.thickness_heads, roughness=self.roughness_head_tail)

        sld_value = self.b_tails.as_unit("Angstrom") / self.vm_tails.as_unit("Angstrom^3")
        sld = ComplexValue(real=sld_value.real, imag=sld_value.imag, unit="1/Angstrom^2")
        composition_tails = Composit(composition={"sld_tails": self.volfrac_t, "solvent_tails": 1.0 - self.volfrac_t})
        composition_tails.resolve_names({"sld_tails": Material(sld=sld), "solvent_tails": self.tail_solvent})
        thickness_tails = Value(
            magnitude=self.thickness.as_unit(self.thickness_heads.unit) - self.thickness_heads.magnitude,
            unit=self.thickness_heads.unit,
        )
        tails = Layer(material=composition_tails, thickness=thickness_tails, roughness=self.roughness_head_tail)

        if self.reverse_monolayer:
            tails.roughness = self.roughness
            return [tails, heads]
        else:
            heads.roughness = self.roughness
            return [heads, tails]
