"""
Implementation of the simplified model language for the ORSO header.

It includes parsing of models from header or different input information and
resolving the model to a simple list of slabs.
"""

from dataclasses import field
from typing import Dict, List, Optional, Union

from .base import Header, Value, ValueRange, ValueVector, orsodataclass


def find_idx(string, start, value):
    res = string[start:].find(value)
    if res >= 0:
        next_idx = start + res
    else:
        next_idx = len(string)
    return next_idx


@orsodataclass
class ModelParameters(Header):
    roughness: Optional[Union[Value, float]] = Value(0.3, 'nm')
    length_units: Optional[str] = 'nm'
    mass_density_units: Optional[str] = 'g/cm^3'
    sld_units: Optional[str] = '1/angstrom^2'
    moment_units: Optional[str] = 'muB'


@orsodataclass
class Material(Header):
    name: str
    formula: Optional[str] = None
    mass_density: Optional[Union[Value, float]] = None
    number_density: Optional[Union[Value, float]] = None
    rel_density: Optional[Union[Value, float]] = None
    sld: Optional[Union[Value, float]] = None
    moment: Optional[Union[Value, float]] = None

    def __post_init__(self):
        Header.__post_init__(self)
        if self.formula is None:
            self.formula = self.name

    def resolve_defaults(self, defaults: ModelParameters):
        if self.mass_density is not None and \
                not isinstance(self.mass_density, Value):
            self.mass_density = Value(self.mass_density,
                                      unit=defaults.mass_density_units)
        if self.sld is not None and \
                not isinstance(self.sld, Value):
            self.sld = Value(self.sld, unit=defaults.sld_units)

        if self.moment is not None and \
                not isinstance(self.moment, Value):
            self.moment = Value(self.moment, unit=defaults.moment_units)


SPECIAL_MATERIALS = {
    'air': Material(name='air', formula='N8O2',
                    number_density=Value(0.)),
    'water': Material(name='water', formula='H2O',
                      mass_density=Value(1., unit='g/cm^3')),
}


@orsodataclass
class Layer(Header):
    name: Optional[str] = None
    material: Optional[str] = None
    thickness: Optional[Union[Value, float]] = None
    roughness: Optional[Union[Value, float]] = None
    formula: Optional[str] = None
    mass_density: Optional[Union[Value, float]] = None
    number_density: Optional[Union[Value, float]] = None
    sld: Optional[Union[Value, float]] = None
    moment: Optional[Union[Value, float]] = None

    def resolve_names(self, resolvable_items):
        if self.material is None:
            return
        if self.material in resolvable_items:
            material = resolvable_items[self.material]
        elif self.material in SPECIAL_MATERIALS:
            material = SPECIAL_MATERIALS[self.material]
        else:
            material = Material(name=self.material,
                                formula=self.material)
        self.formula = material.formula
        self.mass_density = material.mass_density
        self.number_density = material.number_density
        self.sld = material.sld
        self.moment = material.moment

    def resolve_defaults(self, defaults: ModelParameters):
        if self.mass_density is not None and \
                not isinstance(self.mass_density, Value):
            self.mass_density = Value(self.mass_density,
                                      unit=defaults.mass_density_units)
        if self.sld is not None and \
                not isinstance(self.sld, Value):
            self.sld = Value(self.sld, unit=defaults.sld_units)

        if self.moment is not None and \
                not isinstance(self.moment, Value):
            self.moment = Value(self.moment, unit=defaults.moment_units)

        if self.roughness is None:
            self.roughness = defaults.roughness
        elif not isinstance(self.roughness, Value):
            self.roughness = Value(self.roughness, unit=defaults.length_units)

        if self.thickness is None:
            self.thickness = Value(0., unit=defaults.length_units)
        elif not isinstance(self.thickness, Value):
            self.thickness = Value(self.thickness, unit=defaults.length_units)


@orsodataclass
class SubStack(Header):
    name: str
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
                next_idx = find_idx(stack, idx, '|')
                if '(' in stack[idx:next_idx]:
                    close_idx = find_idx(stack, idx, ')')
                    next_idx = find_idx(stack, close_idx, '|')
                    rep, sub_stack = stack[idx:close_idx].split('(', 1)
                    rep = int(rep)
                    obj = SubStack(name=f'multilayer_{idx}',
                                   repetitions=rep, stack=sub_stack.strip())
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
                            obj = Layer(name=item,
                                        formula=obj.formula,
                                        mass_density=obj.mass_density,
                                        number_density=obj.number_density,
                                        thickness=thickness)
                    else:
                        obj = Layer(material=item, thickness=thickness)
                if hasattr(obj, 'resolve_names'):
                    obj.resolve_names(ri)
                output.append(obj)
                idx = next_idx + 1
            output.reverse()
            self.layers = output
        elif self.stack is None:
            raise ValueError("SubStack has to have either layers or stack defined.")

    def resolve_defaults(self, defaults: ModelParameters):
        for li in self.layers:
            if hasattr(li, 'resolve_defaults'):
                li.resolve_defaults(defaults)

    def resolve_to_layers(self):
        layers = list(self.layers)
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                continue
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[:i + added] + sub_layers + layers[i + added:]
                added += len(sub_layers) - 1
        return layers * self.repetitions


@orsodataclass
class SampleModel(Header):
    origin: str
    stack: str
    sub_stacks: Optional[List[SubStack]] = None
    layers: Optional[List[Layer]] = None
    materials: Optional[List[Material]] = None
    globals: Optional[ModelParameters] = ModelParameters()
    reference: Optional[str] = None

    @property
    def resolvable_items(self):
        output = {}
        if self.sub_stacks:
            for si in self.sub_stacks:
                output[si.name] = si
        if self.layers:
            for li in self.layers:
                output[li.name] = li
        if self.materials:
            for mi in self.materials:
                output[mi.name] = mi
        return output

    def resolve_stack(self):
        stack = self.stack
        ri = self.resolvable_items
        output = []
        idx = 0
        while idx < len(stack):
            next_idx = find_idx(stack, idx, '|')
            if '(' in stack[idx:next_idx]:
                close_idx = find_idx(stack, idx, ')')
                next_idx = find_idx(stack, close_idx, '|')
                rep, sub_stack = stack[idx:close_idx].split('(', 1)
                rep = int(rep)
                obj = SubStack(name=f'multilayer_{idx}',
                               repetitions=rep, stack=sub_stack.strip())
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
                        obj = Layer(name=item,
                                    formula=obj.formula,
                                    mass_density=obj.mass_density,
                                    number_density=obj.number_density,
                                    thickness=thickness)
                else:
                    obj = Layer(material=item, thickness=thickness)
            if hasattr(obj, 'resolve_names'):
                obj.resolve_names(ri)
            if hasattr(obj, 'resolve_defaults'):
                obj.resolve_defaults(self.globals)
            output.append(obj)
            idx = next_idx + 1
        output.reverse()
        return output

    def resolve_to_layers(self):
        layers = self.resolve_stack()
        added = 0
        for i in range(len(layers)):
            if isinstance(layers[i + added], Layer):
                continue
            else:
                obj = layers.pop(i + added)
                sub_layers = obj.resolve_to_layers()
                layers = layers[:i + added] + sub_layers + layers[i + added:]
                added += len(sub_layers) - 1
        return layers
