"""
Python script to showcase the simple model language by resolving a stack string
and plotting SLD and reflectivity for neutrons.

Script requires matplotlib and refnx to run.
"""

import sys
import yaml

from orsopy.fileio import model_language
from refnx.reflect import SLD, ReflectModel, Structure
from matplotlib import pyplot
from numpy import linspace

q=linspace(0.001,0.2,200)

def main(txt=None):
    if txt is None:
        txt = sys.argv[1]
    if txt.endswith('.yml'):
        dtxt = yaml.safe_load(open(txt, 'r').read())
        if 'data_source' in dtxt:
            dtxt = dtxt['data_source']
        if 'sample' in dtxt:
            dtxt = dtxt['sample']['model']
        sample = model_language.SampleModel(**dtxt)
    else:
        sample = model_language.SampleModel(stack=txt)
    # initial model before resolving any names
    print(repr(sample), '\n')

    layers = sample.resolve_to_layers()
    structure = Structure()
    for l in reversed(layers):
        m = SLD(l.material.get_sld()*1e6)
        if l.thickness.unit == 'nm':
            structure |= m(l.thickness.magnitude*10., l.roughness.magnitude*10.)
        else:
            structure |= m(l.thickness.magnitude, l.roughness.magnitude)
    model = ReflectModel(structure, bkg=0.)

    print("\n".join([repr(li) for li in layers]))

    pyplot.figure(figsize=(12,5))
    pyplot.subplot(121)
    pyplot.semilogy(q, model(q))
    pyplot.title(txt)
    pyplot.xlabel("q [Å$^{-1}$]")
    pyplot.ylabel("Neutron-reflectivity")
    pyplot.subplot(122)
    pyplot.plot(*structure.sld_profile())
    pyplot.title(txt)
    pyplot.ylabel('SLD /$10^{-6} \AA^{-2}$')
    pyplot.xlabel('distance / $\AA$');
    pyplot.show()

if __name__ == "__main__":
    main()
