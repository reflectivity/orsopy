"""
Python script to showcase the simple model language by resolving a stack string
and plotting SLD and reflectivity for neutrons.

Script requires matplotlib and refnx to run.
"""

import sys

import yaml

from matplotlib import pyplot
from numpy import linspace
from refnx.reflect import SLD, ReflectModel, Structure

from orsopy.fileio import model_language

q = linspace(0.001, 0.2, 200)


def main(txt=None):
    if txt is None:
        txt = sys.argv[1]
    if txt.endswith(".yml"):
        dtxt = yaml.safe_load(open(txt, "r").read())
        if "data_source" in dtxt:
            dtxt = dtxt["data_source"]
        if "sample" in dtxt:
            dtxt = dtxt["sample"]["model"]
        sample = model_language.SampleModel(**dtxt)
    else:
        sample = model_language.SampleModel(stack=txt)
    # initial model before resolving any names
    print(repr(sample), "\n")
    print("\n".join([repr(ss) for ss in sample.resolve_stack()]), "\n")

    layers = sample.resolve_to_layers()
    print("\n".join([repr(li) for li in layers]))

    structure = Structure()
    for lj in reversed(layers):
        m = SLD(lj.material.get_sld() * 1e6)
        structure |= m(lj.thickness.as_unit("angstrom"), lj.roughness.as_unit("angstrom"))
    model = ReflectModel(structure, bkg=0.0)

    pyplot.figure(figsize=(12, 5))
    pyplot.subplot(121)
    pyplot.semilogy(q, model(q))
    pyplot.title(txt)
    pyplot.xlabel("q [Å$^{-1}$]")
    pyplot.ylabel("Neutron-reflectivity")
    pyplot.subplot(122)
    pyplot.plot(*structure.sld_profile())
    pyplot.title(txt)
    pyplot.ylabel("SLD / $10^{-6} \\AA^{-2}$")
    pyplot.xlabel("distance / $\\AA$")
    xlim = pyplot.gca().get_xlim()
    pyplot.xlim(xlim[1], xlim[0])
    pyplot.show()


if __name__ == "__main__":
    main()
