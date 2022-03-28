"""
Implementation of the simplified model language for the ORSO header.

It includes parsing of models from header or different input information and
resolving the model to a simple list of slabs.
"""

from typing import Dict, List, Optional, Union

from .base import Header, Value, orsodataclass


def find_idx(string, start, value):
    res = string[start:].find(value)
    if res >= 0:
        next_idx = start + res
    else:
        next_idx = len(string)
    return next_idx


@orsodataclass
class ModelParameters(Header):
    roughness: Optional[Union[Value, float]] = Value(0.3, "nm")
    length_unit: Optional[str] = "nm"
    mass_density_unit: Optional[str] = "g/cm^3"
    number_density_unit: Optional[str] = "1/nm^3"
    sld_unit: Optional[str] = "1/angstrom^2"
    magnetic_moment_unit: Optional[str] = "muB"


@orsodataclass
class Material(Header):
    formula: Optional[str] = None
    mass_density: Optional[Union[Value, float]] = None
    number_density: Optional[Union[Value, float]] = None
    sld: Optional[Union[Value, float]] = None
    magnetic_moment: Optional[Union[Value, float]] = None

    def resolve_defaults(self, defaults: ModelParameters):
        if self.mass_density is not None and not isinstance(self.mass_density, Value):
            self.mass_density = Value(self.mass_density, unit=defaults.mass_density_unit)
        if self.sld is not None and not isinstance(self.sld, Value):
            self.sld = Value(self.sld, unit=defaults.sld_unit)

        if self.magnetic_moment is not None and not isinstance(self.magnetic_moment, Value):
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

    def get_sld(self):
        if self.sld is not None:
            return self.sld.magnitude
        from orsopy.slddb.material import Formula, Material, get_element

        formula = Formula(self.formula)
        if self.mass_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula], dens=self.mass_density.magnitude
            )
            return material.rho_n
        elif self.number_density is not None:
            material = Material(
                [(get_element(element), amount) for element, amount in formula],
                fu_dens=self.number_density.magnitude * 1e-3,
            )
            return material.rho_n
        else:
            return 0.0


SPECIAL_MATERIALS = {
    "air": Material(formula="N8O2", number_density=Value(0.0)),
    "water": Material(formula="H2O", mass_density=Value(1.0, unit="g/cm^3")),
}


@orsodataclass
class Layer(Header):
    thickness: Optional[Union[Value, float]] = None
    roughness: Optional[Union[Value, float]] = None
    material: Optional[Union[Material, str]] = None
    composition: Optional[Dict[float, Union[Material, str]]] = None

    def resolve_names(self, resolvable_items):
        if self.material is not None:
            if isinstance(self.material, Material):
                pass
            elif self.material in resolvable_items:
                self.material = resolvable_items[self.material]
            elif self.material in SPECIAL_MATERIALS:
                self.material = SPECIAL_MATERIALS[self.material]
            else:
                self.material = Material(formula=self.material)
        elif self.composition is None:
            raise ValueError("Layer has to have either material or composition")
        else:
            for key, value in self.composition.items():
                if value in resolvable_items:
                    material = resolvable_items[value]
                elif value in SPECIAL_MATERIALS:
                    material = SPECIAL_MATERIALS[value]
                else:
                    material = Material(formula=value)
                self.composition[key] = material

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
            for mat in self.composition.values():
                mat.resolve_defaults(defaults)


@orsodataclass
class SubStack(Header):
    repetitions: int = 1
    stack: Optional[str] = None
    layers: Optional[List[Layer]] = None

    def resolve_names(self, resolvable_items):
        if self.layers is None:
            stack = self.stack
            ri = resolvable_items
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

                    if item in ri:
                        obj = ri[item]
                        if isinstance(obj, Material):
                            obj = Layer(material=obj, thickness=thickness)
                    else:
                        obj = Layer(material=item, thickness=thickness)
                if hasattr(obj, "resolve_names"):
                    obj.resolve_names(ri)
                output.append(obj)
                idx = next_idx + 1
            self.layers = output
        # elif self.stack is None:
        #     raise ValueError("SubStack has to have either layers or stack defined.")

    def resolve_defaults(self, defaults: ModelParameters):
        for li in self.layers:
            if hasattr(li, "resolve_defaults"):
                li.resolve_defaults(defaults)

    def resolve_to_layers(self):
        layers = list(self.layers)
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                layers[i + added].material.generate_density()
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[: i + added] + sub_layers + layers[i + added:]
                added += len(sub_layers) - 1
        return layers * self.repetitions


@orsodataclass
class SampleModel(Header):
    stack: str
    origin: Optional[str] = None
    sub_stacks: Optional[Dict[str, SubStack]] = None
    layers: Optional[Dict[str, Layer]] = None
    materials: Optional[Dict[str, Material]] = None
    globals: Optional[ModelParameters] = ModelParameters()
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
        return output

    def resolve_stack(self):
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
                    if isinstance(obj, Material):
                        obj = Layer(material=obj, thickness=thickness)
                else:
                    obj = Layer(material=item, thickness=thickness)
            if hasattr(obj, "resolve_names"):
                obj.resolve_names(ri)
            if hasattr(obj, "resolve_defaults"):
                obj.resolve_defaults(self.globals)
            output.append(obj)
            idx = next_idx + 1
        return output

    def resolve_to_layers(self):
        layers = self.resolve_stack()
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                layers[i + added].material.generate_density()
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[: i + added] + sub_layers + layers[i + added:]
                added += len(sub_layers) - 1
        return layers
