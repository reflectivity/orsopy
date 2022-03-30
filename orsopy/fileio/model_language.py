"""
Implementation of the simplified model language for the ORSO header.

It includes parsing of models from header or different input information and
resolving the model to a simple list of slabs.
"""

from typing import Dict, List, Optional, Union

from .base import ComplexValue, Header, Value, orsodataclass


def find_idx(string, start, value):
    res = string[start:].find(value)
    if res >= 0:
        next_idx = start + res
    else:
        next_idx = len(string)
    return next_idx


@orsodataclass
class ModelParameters(Header):
    roughness: Optional[Union[float, Value]] = Value(0.3, "nm")
    length_unit: Optional[str] = "nm"
    mass_density_unit: Optional[str] = "g/cm^3"
    number_density_unit: Optional[str] = "1/nm^3"
    sld_unit: Optional[str] = "1/angstrom^2"
    magnetic_moment_unit: Optional[str] = "muB"


@orsodataclass
class Material(Header):
    formula: Optional[str] = None
    mass_density: Optional[Union[float, Value]] = None
    number_density: Optional[Union[float, Value]] = None
    sld: Optional[Union[float, ComplexValue, Value]] = None
    magnetic_moment: Optional[Union[float, Value]] = None

    def __post_init__(self):
        super().__post_init__()
        if self.formula is None and self.sld is None:
            raise ValueError("Material has to either define sld or formula")

    def resolve_defaults(self, defaults: ModelParameters):
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
        from orsopy.slddb import api
        from orsopy.slddb.material import Formula

        formula = Formula(self.formula)
        # first search for formula itself
        res = api.search(formula=formula)
        if len(res) > 0:
            m = api.material(res[0]["ID"])
            self.number_density = Value(magnitude=1e3 * m.fu_dens, unit="1/nm^3")
            self.comment = f"density from ORSO SLD db ID={res[0]['ID']}"
            return
        # mix elemental density to approximate alloys
        n = 0.0
        dens = 0.0
        for i in range(len(formula)):
            res = api.search(formula=formula[i][0])
            m = api.material(res[0]["ID"])
            n += formula[i][1]
            dens += 1e3 * m.fu_dens
        dens /= n * len(formula)
        self.number_density = Value(magnitude=dens, unit="1/nm^3")
        self.comment = "density from average element density"

    def get_sld(self) -> complex:
        if self.sld is not None:
            return self.sld.as_unit("1/angstrom^2") + 0j

        from orsopy.slddb.material import Formula, Material, get_element

        formula = Formula(self.formula)
        if self.mass_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula],
                dens=self.mass_density.as_unit("g/cm^3"),
            )
            return material.rho_n
        elif self.number_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula],
                fu_dens=self.number_density.as_unit("1/angstrom^3"),
            )
            return material.rho_n
        else:
            return 0.0j


@orsodataclass
class Composit(Header):
    composition: Dict[str, float]

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

    def generate_density(self):
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

    def get_sld(self):
        return self.material.get_sld()


SPECIAL_MATERIALS = {
    "vacuum": Material(sld=ComplexValue(real=0.0, imag=0.0, unit="1/angstrom^2")),
    "air": Material(formula="N8O2", mass_density=Value(1.225, unit="kg/m^3")),
    "water": Material(formula="H2O", mass_density=Value(1.0, unit="g/cm^3")),
}


@orsodataclass
class Layer(Header):
    thickness: Optional[Union[float, Value]] = None
    roughness: Optional[Union[float, Value]] = None
    material: Optional[Union[Material, Composit, str]] = None
    composition: Optional[Dict[str, float]] = None

    def resolve_names(self, resolvable_items):
        if self.material is not None:
            if isinstance(self.material, Material):
                pass
            elif isinstance(self.material, Composit):
                self.material.resolve_names(resolvable_items)
            elif self.material in resolvable_items:
                self.material = resolvable_items[self.material]
            elif self.material in SPECIAL_MATERIALS:
                self.material = SPECIAL_MATERIALS[self.material]
            else:
                self.material = Material(formula=self.material)
        elif self.composition is None:
            raise ValueError("Layer has to have either material or composition")
        else:
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
        if self.roughness is None:
            self.roughness = defaults.roughness
        elif not isinstance(self.roughness, Value):
            self.roughness = Value(self.roughness, unit=defaults.length_unit)

        if self.thickness is None:
            self.thickness = Value(0.0, unit=defaults.length_unit)
        elif not isinstance(self.thickness, Value):
            self.thickness = Value(self.thickness, unit=defaults.length_unit)

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


@orsodataclass
class SubStack(Header):
    repetitions: int = 1
    stack: Optional[str] = None
    sequence: Optional[List[Layer]] = None
    represents: Optional[str] = None

    def resolve_names(self, resolvable_items):
        if self.sequence is None:
            stack = self.stack
            output = []
            idx = 0
            while idx < len(stack):
                next_idx = find_idx(stack, idx, "|")
                if "(" in stack[idx:next_idx]:
                    close_idx = find_idx(stack, idx, ")")
                    next_idx = find_idx(stack, close_idx, "|")
                    rep, sub_stack = stack[idx:close_idx].split("(", 1)
                    rep = int(rep)
                    obj = SubStack(name=f"multilayer_{idx}", repetitions=rep, stack=sub_stack.strip())
                else:
                    items = stack[idx:next_idx].strip().rsplit(None, 1)
                    item = items[0].strip()
                    if len(items) == 2:
                        thickness = float(items[1])
                    else:
                        thickness = 0.0

                    if item in resolvable_items:
                        obj = resolvable_items[item]
                        if isinstance(obj, Material) or isinstance(obj, Composit):
                            obj = Layer(material=obj, thickness=thickness)
                    else:
                        obj = Layer(material=item, thickness=thickness)
                if hasattr(obj, "resolve_names"):
                    obj.resolve_names(resolvable_items)
                output.append(obj)
                idx = next_idx + 1
            self.sequence = output
        else:
            for li in self.sequence:
                li.resolve_names(resolvable_items)

    def resolve_defaults(self, defaults: ModelParameters):
        for li in self.sequence:
            if hasattr(li, "resolve_defaults"):
                li.resolve_defaults(defaults)

    def resolve_to_layers(self):
        layers = list(self.sequence)
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                if layers[i + added].material is None:
                    layers[i + added].generate_material()
                layers[i + added].material.generate_density()
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[: i + added] + sub_layers + layers[i + added :]
                added += len(sub_layers) - 1
        return layers * self.repetitions


@orsodataclass
class SampleModel(Header):
    stack: str
    origin: Optional[str] = None
    sub_stacks: Optional[Dict[str, SubStack]] = None
    layers: Optional[Dict[str, Layer]] = None
    materials: Optional[Dict[str, Material]] = None
    composits: Optional[Dict[str, Composit]] = None
    globals: Optional[ModelParameters] = None
    reference: Optional[str] = None

    @property
    def resolvable_items(self):
        output = {}
        if self.sub_stacks:
            output.update(self.sub_stacks)
        if self.layers:
            output.update(self.layers)
        if self.materials:
            output.update(self.materials)
        if self.composits:
            output.update(self.composits)
        return output

    def resolve_stack(self):
        if self.globals is None:
            defaults = ModelParameters()
        else:
            defaults = self.globals
        stack = self.stack
        ri = self.resolvable_items
        output = []
        idx = 0
        while idx < len(stack):
            next_idx = find_idx(stack, idx, "|")
            if "(" in stack[idx:next_idx]:
                close_idx = find_idx(stack, idx, ")")
                next_idx = find_idx(stack, close_idx, "|")
                rep, sub_stack = stack[idx:close_idx].split("(", 1)
                rep = int(rep)
                obj = SubStack(repetitions=rep, stack=sub_stack.strip())
            else:
                items = stack[idx:next_idx].strip().rsplit(None, 1)
                item = items[0].strip()
                if len(items) == 2:
                    thickness = float(items[1])
                else:
                    thickness = 0.0

                if item in ri:
                    obj = ri[item]
                    if isinstance(obj, Material) or isinstance(obj, Composit):
                        obj = Layer(material=obj, thickness=thickness)
                else:
                    obj = Layer(material=item, thickness=thickness)
            if hasattr(obj, "resolve_names"):
                obj.resolve_names(ri)
            if hasattr(obj, "resolve_defaults"):
                obj.resolve_defaults(defaults)
            output.append(obj)
            idx = next_idx + 1
        return output

    def resolve_to_layers(self):
        layers = self.resolve_stack()
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                if layers[i + added].material is None:
                    layers[i + added].generate_material()
                layers[i + added].material.generate_density()
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[: i + added] + sub_layers + layers[i + added :]
                added += len(sub_layers) - 1
        return layers
