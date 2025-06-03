from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ..utils.chemical_formula import Formula
from ..utils.density_resolver import MaterialResolver
from .base import ComplexValue, Header, Value

DENSITY_RESOLVERS: List[MaterialResolver] = []


class SubStackType(ABC):
    # Protocol for all items that can be placed in sub_stack

    @property
    @abstractmethod
    def sub_stack_class(self) -> str: ...

    @abstractmethod
    def resolve_names(self, resolvable_items): ...

    @abstractmethod
    def resolve_defaults(self, defaults: "ModelParameters"): ...

    @abstractmethod
    def resolve_to_layers(self) -> List["Layer"]: ...


SUBSTACK_TYPES: List[SubStackType] = []  # keep track of all classes allowed as sub_stack in model


@dataclass
class ModelParameters(Header):
    roughness: Value = field(default_factory=lambda: Value(0.3, "nm"))
    length_unit: str = "nm"
    mass_density_unit: str = "g/cm^3"
    number_density_unit: str = "1/nm^3"
    sld_unit: str = "1/angstrom^2"
    magnetic_moment_unit: str = "muB"


@dataclass
class Material(Header):
    formula: Optional[str] = None
    mass_density: Optional[Union[float, Value]] = None
    number_density: Optional[Union[float, Value]] = None
    sld: Optional[Union[float, ComplexValue, Value]] = None
    magnetic_moment: Optional[Union[float, Value]] = None
    relative_density: Optional[float] = None

    original_name = None

    def resolve_defaults(self, defaults: ModelParameters):
        if self.formula is None and self.sld is None:
            if self.original_name is None:
                raise ValueError("Material has to either define sld or formula")
            else:
                self.formula = self.original_name
        if self.mass_density is not None:
            if isinstance(self.mass_density, Value) and self.mass_density.unit is None:
                self.mass_density.unit = defaults.mass_density_unit
            elif not isinstance(self.mass_density, Value):
                self.mass_density = Value(self.mass_density, unit=defaults.mass_density_unit)
        if self.number_density is not None:
            if isinstance(self.number_density, Value) and self.number_density.unit is None:
                self.number_density.unit = defaults.number_density_unit
            elif not isinstance(self.number_density, Value):
                self.number_density = Value(self.number_density, unit=defaults.number_density_unit)
        if self.sld is not None:
            if isinstance(self.sld, (Value, ComplexValue)) and self.sld.unit is None:
                self.sld.unit = defaults.sld_unit
            elif not isinstance(self.sld, (Value, ComplexValue)):
                self.sld = Value(self.sld, unit=defaults.sld_unit)
        if self.magnetic_moment is not None:
            if isinstance(self.magnetic_moment, Value) and self.magnetic_moment.unit is None:
                self.magnetic_moment.unit = defaults.magnetic_moment_unit
            elif not isinstance(self.magnetic_moment, Value):
                self.magnetic_moment = Value(self.magnetic_moment, unit=defaults.magnetic_moment_unit)

    def generate_density(self):
        if self.sld is not None or self.mass_density is not None or self.number_density is not None:
            # this material already contains density information
            return
        if len(DENSITY_RESOLVERS) == 0:
            from ..utils.resolver_slddb import ResolverSLDDB

            DENSITY_RESOLVERS.append(ResolverSLDDB())

        if self.formula in CACHED_MATERIALS:
            self.number_density = CACHED_MATERIALS[self.formula][0]
            self.comment = CACHED_MATERIALS[self.formula][1]
            return

        formula = Formula(self.formula)
        # first search for formula itself
        for ri in DENSITY_RESOLVERS:
            try:
                dens = ri.resolve_formula(formula)
            except ValueError:
                pass
            else:
                self.number_density = Value(magnitude=dens, unit="1/nm^3")
                self.comment = ri.comment
                CACHED_MATERIALS[self.formula] = (self.number_density, ri.comment)
                return
        # mix elemental density to approximate alloys
        for ri in DENSITY_RESOLVERS:
            try:
                dens = ri.resolve_elemental(formula)
            except ValueError:
                pass
            else:
                self.number_density = Value(magnitude=dens, unit="1/nm^3")
                self.comment = ri.comment
                CACHED_MATERIALS[self.formula] = (self.number_density, ri.comment)
                return
        self.number_density = Value(magnitude=0.0, unit="1/nm^3")
        self.comment = "could not locate density information for material"

    def get_sld(self, xray_energy=None) -> complex:
        if self.relative_density is None:
            rel = 1.0
        else:
            rel = self.relative_density
        if self.sld is not None:
            return rel * self.sld.as_unit("1/angstrom^2") + 0j

        from orsopy.slddb.material import Material, get_element

        formula = Formula(self.formula)
        if self.mass_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula],
                dens=self.mass_density.as_unit("g/cm^3"),
            )
            if xray_energy is None:
                return rel * material.rho_n
            else:
                return rel * material.rho_of_E(xray_energy)
        elif self.number_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula],
                fu_dens=self.number_density.as_unit("1/angstrom^3"),
            )
            if xray_energy is None:
                return rel * material.rho_n
            else:
                return rel * material.rho_of_E(xray_energy)
        else:
            return 0.0j


@dataclass
class Composit(Header):
    composition: Dict[str, float]

    original_name = None

    def resolve_names(self, resolvable_items):
        self._composition_materials = {}
        for key, value in self.composition.items():
            if key in resolvable_items:
                material = resolvable_items[key]
            elif key in SPECIAL_MATERIALS:
                material = SPECIAL_MATERIALS[key]
            else:
                material = Material(formula=key)
            self._composition_materials[key] = material

    def resolve_defaults(self, defaults: ModelParameters):
        for mat in self._composition_materials.values():
            mat.resolve_defaults(defaults)

    def generate_density(self, xray_energy=None):
        """
        Create a material based on the composition attribute.
        """
        sld = 0.0
        for key, value in self.composition.items():
            mi = self._composition_materials[key]
            mi.generate_density()
            sldi = mi.get_sld(xray_energy=xray_energy)
            sld += value * sldi
        mix_str = ";".join([f"{value}x{key}" for key, value in self.composition.items()])
        return Material(
            sld=ComplexValue(real=sld.real, imag=sld.imag, unit="1/angstrom^2"),
            comment=f"composition material: {mix_str}",
        )

    def get_sld(self, xray_energy=None):
        material = self.generate_density(xray_energy=xray_energy)
        return material.get_sld(xray_energy=xray_energy)


SPECIAL_MATERIALS = {
    "vacuum": Material(sld=ComplexValue(real=0.0, imag=0.0, unit="1/angstrom^2")),
    "air": Material(formula="N8O2", mass_density=Value(1.225, unit="kg/m^3")),
    "water": Material(formula="H2O", mass_density=Value(1.0, unit="g/cm^3")),
}
CACHED_MATERIALS = {}


@dataclass
class Layer(Header):
    thickness: Optional[Union[float, Value]] = None
    roughness: Optional[Union[float, Value]] = None
    material: Optional[Union[Material, Composit, str]] = None
    composition: Optional[Dict[str, float]] = None

    original_name = None

    def resolve_names(self, resolvable_items):
        if self.material is None and self.composition is None and self.original_name is None:
            raise ValueError("Layer has to either define material or composition")
        if self.material is not None:
            if isinstance(self.material, Material):
                pass
            elif isinstance(self.material, Composit):
                self.material.resolve_names(resolvable_items)
            elif self.material in resolvable_items:
                possible_material = resolvable_items[self.material]
                if isinstance(possible_material, Layer):
                    # There was another layer that used a formula as name
                    # fall back to formula from material name.
                    self.material = Material(formula=self.material)
                else:
                    self.material = possible_material
            elif self.material in SPECIAL_MATERIALS:
                self.material = SPECIAL_MATERIALS[self.material]
            else:
                self.material = Material(formula=self.material)
        elif self.composition:
            self._composition_materials = {}
            for key, value in self.composition.items():
                if key in resolvable_items:
                    material = resolvable_items[key]
                elif key in SPECIAL_MATERIALS:
                    material = SPECIAL_MATERIALS[key]
                else:
                    material = Material(formula=key)
                self._composition_materials[key] = material
        else:
            self.material = Material(formula=self.original_name)

    def resolve_defaults(self, defaults: ModelParameters):
        if self.roughness is None:
            self.roughness = defaults.roughness
        elif not isinstance(self.roughness, Value):
            self.roughness = Value(self.roughness, unit=defaults.length_unit)
        elif self.roughness.unit is None:
            self.roughness.unit = defaults.length_unit

        if self.thickness is None:
            self.thickness = Value(0.0, unit=defaults.length_unit)
        elif not isinstance(self.thickness, Value):
            self.thickness = Value(self.thickness, unit=defaults.length_unit)
        elif self.thickness.unit is None:
            self.thickness.unit = defaults.length_unit

        if self.material is not None:
            self.material.resolve_defaults(defaults)
        else:
            for mat in self._composition_materials.values():
                mat.resolve_defaults(defaults)

    def generate_material(self):
        """
        Create a material based on the composition attribute.
        """
        sld = 0.0
        for key, value in self.composition.items():
            mi = self._composition_materials[key]
            mi.generate_density()
            sldi = mi.get_sld()
            sld += value * sldi
        mix_str = ";".join([f"{value}x{key}" for key, value in self.composition.items()])
        self.material = Material(
            sld=ComplexValue(real=sld.real, imag=sld.imag, unit="1/angstrom^2"),
            comment=f"composition material: {mix_str}",
        )
