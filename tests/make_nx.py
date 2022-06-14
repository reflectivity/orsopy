import os
from orsopy.fileio import load_orso
from orsopy.fileio.orso import save_nexus

currdir = os.path.dirname(__file__)
ex = load_orso(os.path.join(currdir, "test_example2.ort"))
# for entry in ex:
#    entry.data = entry.data.T

save_nexus(ex, os.path.join(currdir, "test_nexus.orb"))
