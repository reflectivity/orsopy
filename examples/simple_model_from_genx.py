"""
Example how to export a GenX sample model to the simple model language.
"""

import os
import sys

from genx import api
# improve load time by ignoring numba
from genx.models import lib as gmlib

from orsopy.fileio import model_language as ml

gmlib.USE_NUMBA = False


def get_materialn(li):
    sld = li.b * li.dens + 0j
    return ml.Material(sld=ml.ComplexValue(sld.real, sld.imag, "1/angstrom^2"))


def get_materialx(li):
    sld = li.f * li.dens + 0j
    return ml.Material(sld=ml.ComplexValue(sld.real, sld.imag, "1/angstrom^2"))


get_material = get_materialn


def get_layer(li):
    return ml.Layer(thickness=li.d, material=get_material(li), roughness=li.sigma)


def main():
    fname = sys.argv[1]
    model, optimizer = api.load(fname)
    model.compile_script()
    sm = model.script_module

    global get_material
    if sm.inst.probe == "x-ray":
        get_material = get_materialx

    names = list(sm.__dict__.keys())
    objects = list(sm.__dict__.values())

    defaults = ml.ModelParameters(length_unit="angstrom", number_density_unit="1/angstrom^3")
    layers = {}
    materials = {}
    materials["ambient"] = get_material(sm.Amb)
    materials["substrate"] = get_material(sm.Sub)
    sub_stacks = {}
    stack_order = ["ambient"]
    for si in sm.sample.Stacks:
        if len(si.Layers) == 0:
            continue
        ni = names[objects.index(si)]
        stack_order.append(ni)

        layer_order = []
        for lj in si.Layers:
            nj = names[objects.index(lj)]
            layers[nj] = get_layer(lj)
            layer_order.append(nj)
        sub_stacks[ni] = ml.SubStack(repetitions=si.Repetitions, stack=" | ".join(layer_order))
    stack_order.append("substrate")
    stack_str = " | ".join(stack_order)

    sample = ml.SampleModel(
        stack=stack_str,
        origin=f'GenX model "{os.path.basename(fname)}"',
        sub_stacks=sub_stacks,
        layers=layers,
        materials=materials,
        globals=defaults,
    )
    print(sample.to_yaml())


if __name__ == "__main__":
    main()
