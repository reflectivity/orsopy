import datetime
import json
import os
import pathlib
import ssl
import warnings

from urllib import parse, request
from urllib.error import URLError

from . import DB_FILE, SLDDB
from .dbconfig import WEBAPI_URL, DB_MATERIALS_FIELDS, DB_MATERIALS_HIDDEN_DATA, db_lookup
from .blender import collect_protein, collect_dna, collect_rna
from .element_table import get_element
from .material import Formula, Material


class SLD_API:
    """
    Python API for users of the SLDDB data.

    Allows to query the online database for materials, calculate SLDs and add new materials.
    If connection to the server fails, a local copy of the database is used, instead.

    Usage:
      from orsopy.slddb import api
      res=api.search(formula="Fe2O3")
      res[0]['density'] => ....

      m=api.material(res[0]['ID']) # retrieve all data for the given material, see Material class.
      sldn=m.rho_n # get nuclear neutron SLD (complex number)
      sldm=m.rho_m # get magnetic neutron SLD (real number)
      sldx=m.f_of_E(E=8.047823) # get x-ray SLD (complex number) for given energy, default is Cu-Kalpha

      # custom material just for SLD calculation, requires either dens, fu_volume, rho_n or xsld+xE
      m=api.custom(formula='Au', dens=19.3)

    Units of results/queries:
      density: g/cm³
      roh_n: Å^{-2}
      roh_m: Å^{-2}
      sldx: Å^{-2}
      fu_volume: Å³
    """

    db_suburl = "download_db"
    max_age = 1
    db: SLDDB = None

    def __init__(self, update_db=True):
        self.update_db = update_db
        self.use_webquery = False  # default to using local database, which is updated regularly

    def check(self):
        # make sure the local database file is up to date, if not try to download newest version
        if self.update_db:
            now = datetime.datetime.now()
            try:
                stat = pathlib.Path(DB_FILE).stat()
            except FileNotFoundError:
                self.download_db()
            else:
                mtime = datetime.datetime.fromtimestamp(stat.st_ctime)
                try:
                    mtime = max(mtime, datetime.datetime.fromtimestamp(stat.st_mtime))
                except AttributeError:
                    pass
                if (now - mtime).days > self.max_age:
                    try:
                        self.download_db()
                    except URLError as err:
                        warnings.warn("Can't download new version of database; " + str(err))
            self.db = SLDDB(DB_FILE)  # after potential update, make connection with local database
            self.update_db = False
        else:
            return

    def download_db(self):
        # noinspection PyUnresolvedReferences
        context = ssl._create_unverified_context()
        res = request.urlopen(WEBAPI_URL + self.db_suburl, context=context)
        data = res.read()
        if not data.startswith(b"SQLite format 3"):
            raise ValueError("Error when downloading new database")
        if os.path.isfile(DB_FILE):
            os.remove(DB_FILE)
        with open(DB_FILE, "wb") as fh:
            fh.write(data)

    @staticmethod
    def webquery(qdict):
        data = parse.urlencode(qdict)
        # noinspection PyUnresolvedReferences
        context = ssl._create_unverified_context()
        webdata = request.urlopen(WEBAPI_URL + "api?" + data, context=context)
        return json.loads(webdata.read())  # return decoded data

    def localquery(self, qdict):
        return query_api(qdict)

    def search(self, **opts):
        """
        Search for a particular material using a combination of provided search keys.

        Examples:
             api.search(formula="Fe2O3")
             api.search(density=5.242)
             api.search(name='iron')
        """
        if not self.use_webquery:
            return self.localquery(opts)

        self.check()
        try:
            res = self.webquery(opts)
        except URLError:
            self.use_webquery = False
            res = self.localquery(opts)
        return res

    def material(self, ID):
        """
        Returns the material object for a certain database entry specified by its unique ID.

        Example:
            res=api.search(formula='Fe')
            material=api.material(res[0]['ID'])
            print(material.dens, material.rho_n, material.f_of_E(8.0))
        """

        res = self.search(ID=int(ID))

        f = Formula(res["formula"], sort=False)
        mat_data = dict(dens=float(res["density"]), ID=ID, extra_data={})
        if res.get("name", None):
            mat_data["name"] = res["name"]
        if res.get("mu", 0.0):
            mat_data["mu"] = res["mu"]
        elif res.get("M", 0.0):
            mat_data["M"] = res["M"]
        for key in ["ORSO_validated", "description", "doi", "reference"]:
            if key in res:
                mat_data["extra_data"][key] = res[key]
        out = Material([(get_element(element), amount) for element, amount in f], **mat_data)
        return out

    @staticmethod
    def custom(formula, dens=None, fu_volume=None, rho_n=None, mu=0.0, xsld=None, xE=None):
        """
        Returns the material object for a certain material as specified by caller.

        Example:
            res=api.custom('Fe', dens=7.8)
            print(material.dens, material.rho_n, material.f_of_E(8.0))
        """
        f = Formula(formula, sort=False)
        out = Material(
            [(get_element(element), amount) for element, amount in f],
            dens=dens,
            fu_volume=fu_volume,
            rho_n=rho_n,
            mu=mu,
            xsld=xsld,
            xE=xE,
        )
        return out

    def bio_blender(self, sequence, molecule="protein"):
        """
        Get material for protein, DNA or RNA. Provide a letter sequence and molecule type ('protein', 'dna', 'rna').
        """
        opts = {molecule.lower(): sequence, "sldcalc": "true"}
        res = self.search(**opts)
        mat_data = dict(fu_volume=float(res["fu_volume"]), name=f"BioBlender-{molecule.lower()}", extra_data={})
        for key in [
            "description",
        ]:
            if key in res:
                mat_data["extra_data"][key] = res[key]

        out = Material(Formula(res["formula"]), **mat_data)
        return out


# webquery API functions:
def calc_api(args):
    """Calculate SLD from formula/density or biological sequence.

    args: dict-like with optional keys: formula, density, protein, dna, rna,
          name, material_description, xray_unit.
    Returns a JSON string.
    """
    if 'protein' in args:
        try:
            material = collect_protein(args['protein'])
        except Exception as e:
            return repr(e)
        else:
            name = args.get('name', 'protein')
    elif 'dna' in args:
        try:
            material = collect_dna(args['dna'])
        except Exception as e:
            return repr(e)
        else:
            name = args.get('name', 'DNA')
    elif 'rna' in args:
        try:
            material = collect_rna(args['rna'])
        except Exception as e:
            return repr(e)
        else:
            name = args.get('name', 'RNA')
    elif 'formula' in args and 'density' in args:
        f = Formula(args['formula'], sort=False)
        try:
            material = Material(f, dens=float(args['density']))
        except Exception as e:
            return repr(e)
        else:
            name = args.get('name', 'User Query')
    else:
        return 'Could not calculate, missing formula and density or protein/dna/rna sequence'
    material.name = name
    if args.get('material_description', '') != '':
        material.extra_data['description'] = args['material_description']
    out = material.export(xray_units=args.get('xray_unit', 'edens'))
    return out


def select_api(args):
    """Return JSON for a material selected by ID.

    args: dict-like with keys: ID, and optionally xray_unit.
    Returns a JSON string.
    """
    db = SLDDB(DB_FILE)
    res = db.search_material(filter_invalid=False, ID=int(args['ID']))
    try:
        material = db.select_material(res[0])
    except IndexError:
        return '## ID not found in database'
    except Exception as e:
        return repr(e) + '<br >' + "Raised when tried to parse material = %s" % res[0]
    out = material.export(xray_units=args.get('xray_unit', 'edens'))
    return out

def search_api(args):
    """Search the database with the given field values.

    args: dict-like mapping DB field names to query values.
    Returns a JSON string.
    """
    query = {}
    for key, value in args.items():
        if str(value).strip() == '':
            continue
        if key in DB_MATERIALS_FIELDS:
            try:
                query[key] = db_lookup[key][1].convert(str(value))
            except Exception as e:
                return repr(e) + '<br >' + "Raised when tried to parse %s = %s" % (key, value)
    db = SLDDB(DB_FILE)
    res = db.search_material(serializable=True, limit=10000, **query)

    # remove hidden database fields besides ORSO validation
    for ri in res:
        for field in DB_MATERIALS_HIDDEN_DATA:
            if field.startswith('validated'):
                continue
            del ri[field]

    return res


def query_api(args):
    """Dispatch an API request based on which keys are present in args.

    args: dict-like (e.g. request.args or a plain dict).
    Returns a JSON string.
    """
    if 'ID' in args:
        return select_api(args)
    elif 'sldcalc' in args:
        return calc_api(args)
    elif 'get_fields' in args:
        return [
            field for field in DB_MATERIALS_FIELDS if field not in DB_MATERIALS_HIDDEN_DATA
        ]
    else:
        return search_api(args)