"""
Implementation of DensityResolver using SLD DB queries.
"""

from ..slddb import api
from .chemical_formula import Formula
from .density_resolver import MaterialResolver


class ResolverSLDDB(MaterialResolver):
    comment = ""

    def resolve_item(self, name):
        if name.startswith("ID="):
            try:
                ID = int(name[3:])
            except ValueError:
                pass
            else:
                m = api.material(ID)
                self.comment = f"material from ORSO SLD db ID={ID}"
                out = {
                    "formula": m.formula,
                    "number_density": 1e3 * m.fu_dens,
                    "comment": self.comment,
                }
                return out

        res = api.search(name=name)
        for ri in res:
            if ri["name"].lower() == name.lower():
                m = api.material(ri["ID"])
                self.comment = f"material '{ri['name']}' from ORSO SLD db ID={res[0]['ID']}"
                out = {
                    "formula": m.formula,
                    "number_density": 1e3 * m.fu_dens,
                    "comment": self.comment,
                }
                return out
        return None

    def resolve_formula(self, formula: Formula) -> float:
        res = api.search(formula=formula)
        if len(res) > 0:
            m = api.material(res[0]["ID"])
            self.comment = f"density from ORSO SLD db ID={res[0]['ID']}"
            return 1e3 * m.fu_dens
        else:
            raise ValueError(f"Could not find material {formula}")

    def resolve_elemental(self, formula: Formula) -> float:
        n = 0.0
        dens = 0.0
        for i in range(len(formula)):
            res = api.search(formula=formula[i][0])
            if len(res) == 0:
                raise ValueError(f"Could not find element {formula[i][0]}")
            m = api.material(res[0]["ID"])
            n += formula[i][1]
            dens += 1e3 * m.fu_dens
        dens /= n * len(formula)
        self.comment = "density from average element density from ORSO SLD db"
        return dens
