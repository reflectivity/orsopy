"""
Pure calculation functions for combining biological sequences and material blends.
No web-framework dependencies.
"""

from .dbconfig import DB_FILE
from .database import SLDDB
from .material import Material
from .element_table import get_element
from .comparators import ExactString

AMINO_ABRV = {
    "A": "Alanine",
    "R": "Arginine",
    "N": "Asparagine",
    "D": "Aspartate",
    "B": "Aspartate",
    "C": "Cysteine",
    "E": "Glutamate",
    "Q": "Glutamine",
    "Z": "Glutamate",
    "G": "Glycine",
    "H": "Histidine",
    "I": "Isoleucine",
    "L": "Leucine",
    "K": "Lysine",
    "M": "Methionine",
    "F": "Phenylalanine",
    "P": "Proline",
    "S": "Serine",
    "T": "Threonine",
    "W": "Tryptophan",
    "Y": "Tyrosine",
    "V": "Valine",
}

RNA_ABRV = {
    "A": "RNA-Adenine",
    "G": "RNA-Guanine",
    "C": "RNA-Cytosine",
    "U": "RNA-Uracil",
}

DNA_ABRV = {
    "A": "DNA-Adenine",
    "G": "DNA-Guanine",
    "C": "DNA-Cytosine",
    "T": "DNA-Thymine",
}


class SequenceParseError(ValueError):
    pass


def clean_str(string):
    return string.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip()


hx2o = Material([(get_element(element), amount) for element, amount in [('Hx', 2.0), ('O', 1.0)]], dens=1.0)


def collect_combination(ids, name_dict):
    db = SLDDB(DB_FILE)
    elements: list[Material] = []
    loaded_ids: dict[str, Material] = {}
    for id in ids:
        if id not in loaded_ids:
            try:
                entry = db.search_material(name=ExactString(name_dict[id]))[0]
            except KeyError:
                possible_ids = name_dict.keys()
                raise SequenceParseError(f"Not a valid identifier {id}, options are {''.join(possible_ids)}")
            except IndexError:
                raise SequenceParseError(f"Molecule {name_dict[id]} not found in database")
            m = db.select_material(entry)
            loaded_ids[id] = m
        elements.append(loaded_ids[id])
    result = elements[0]
    for element in elements[1:]:
        result += element
    return result


def collect_protein(acids):
    acids = clean_str(acids).upper()
    result = collect_combination(acids, AMINO_ABRV) + hx2o
    result.extra_data['description'] = f'protein - {len(acids)} residues'
    return result


def collect_dna(bases):
    bases = clean_str(bases).upper()
    result = collect_combination(bases, DNA_ABRV) + hx2o
    result.extra_data['description'] = f'DNA - {len(bases)} residues'
    return result


def collect_rna(bases):
    bases = clean_str(bases).upper()
    result = collect_combination(bases, RNA_ABRV) + hx2o
    result.extra_data['description'] = f'RNA - {len(bases)} residues'
    return result


def collect_blendIDs(formula):
    db = SLDDB(DB_FILE)
    elements: list[Material] = []
    loaded_ids = {}
    items = []
    while '(' in clean_str(formula):
        pre, formula = formula.split(')', 1)
        number = float(pre.split('*', 1)[0].strip('(').strip())
        ID = int(pre.split('*', 1)[1].strip())
        items.append((number, ID))
    for number, ID in items:
        if ID not in loaded_ids:
            entry = db.search_material(ID=ID)[0]
            m = db.select_material(entry)
            loaded_ids[ID] = m
        elements.append(number * loaded_ids[ID])
    result = elements[0]
    for element in elements[1:]:
        result += element
    return result


def collect_blend(mtype, idstr):
    if mtype == 'protein':
        return collect_protein(idstr)
    elif mtype == 'dna':
        return collect_dna(idstr)
    elif mtype == 'rna':
        return collect_rna(idstr)
    elif mtype == 'db':
        return collect_blendIDs(idstr)
