"""
A simple class to resolve and store chemical formula strings.
"""

import re

from collections import OrderedDict


class Formula(list):
    """
    Evaluate strings for element chemical formula.
    """

    elements = (
        r"A[cglmrstu]|B[aehikr]?|C[adeflmorsu]?|D[bsy]{0,1}|E[rsu]|F[emr]?|"
        r"G[ade]|H[efgosx]?|I[nr]?|Kr?|L[airu]|M[dgnot]|N[abdeiop]?|"
        r"Os?|P[abdmortu]?|R[abefghnu]|S[bcegimnr]?|T[abcehilm]|"
        r"Uu[bhopqst]|U|V|W|Xe|Yb?|Z[nr]"
    )
    isotopes = (
        r"(A[cglmrstu]|B[aehikr]?|C[adeflmorsu]?|D[bsy]{0,1}|E[rsu]|F[emr]?|"
        r"G[ade]|H[efgos]?|I[nr]?|Kr?|L[airu]|M[dgnot]|N[abdeiop]?|"
        r"Os?|P[abdmortu]?|R[abefghnu]|S[bcegimnr]?|T[abcehilm]|"
        r"Uu[bhopqst]|U|V|W|Xe|Yb?|Z[nr])"
        r"\[[1-9][0-9]{0,2}\]"
    )

    def __init__(self, string, sort=True):
        if isinstance(string, list):
            list.__init__(self, string)
            if isinstance(string, Formula):
                self._do_sort = string._do_sort
                self.HR_formula = string.HR_formula
            else:
                self._do_sort = sort
                self.HR_formula = str(self)
        else:
            self._do_sort = sort
            self.HR_formula = string
            list.__init__(self, [])
            self.parse_string(string)
            self.merge_same()

    def parse_string(self, string):
        # remove gaps and ignored characters
        string = string.replace(" ", "").replace("\t", "").replace("\n", "")
        string = string.replace("{", "").replace("}", "").replace("_", "").replace("$", "")

        groups = self.split_groups(string)
        for group, factor in groups:
            try:
                items = self.parse_group(group, case_sensitive=True)
            except ValueError:
                items = self.parse_group(group, case_sensitive=False)
            items = [(i[0], i[1] * factor) for i in items]
            # noinspection PyMethodFirstArgAssignment
            self += items

    @staticmethod
    def split_groups(string):
        if "(" not in string:
            return [(string, 1.0)]
        out = []
        start = string.index("(")
        end = start
        if start > 0:
            out.append((string[:start], 1.0))
        while end < len(string):
            end = start + string[start:].find(")")
            _next = end + 1
            if end < start:
                raise ValueError("Brackets need to be closed")
            while not (_next == len(string) or string[_next].isalpha() or string[_next] == "("):
                _next += 1
            block = string[start + 1 : end]
            if "(" in block:
                raise ValueError("Only one level of brackets is allowed")
            number = string[end + 1 : _next]
            if number == "":
                out.append((block, 1.0))
            else:
                out.append((block, float(number)))
            if _next == len(string):
                break
            if "(" not in string[_next:]:
                out.append((string[_next:], 1.0))
                break
            else:
                start = _next + string[_next:].index("(")
                end = start
                if start > _next:
                    out.append((string[_next:start], 1.0))
        return out

    def parse_group(self, group, case_sensitive=True):
        if case_sensitive:
            flags = 0
        else:
            flags = re.IGNORECASE
        out = []
        mele = re.search(self.elements, group, flags=flags)
        miso = re.search(self.isotopes, group, flags=flags)
        if miso is not None and miso.start() == mele.start():
            prev = miso
        else:
            prev = mele
        if prev is None or prev.start() != 0:
            raise ValueError("Did not find any valid element in string")
        pos = prev.end()
        while pos < len(group):
            mele = re.search(self.elements, group[pos:], flags=flags)
            miso = re.search(self.isotopes, group[pos:], flags=flags)
            if miso is not None and miso.start() == mele.start():
                _next = miso
            else:
                _next = mele
            if _next is None:
                break
            if _next.start() == 0:
                out.append((prev.string[prev.start() : prev.end()].capitalize(), 1.0))
            else:
                out.append(
                    (prev.string[prev.start() : prev.end()].capitalize(), float(group[pos : pos + _next.start()]))
                )
            prev = _next
            pos += _next.end()
        if pos == len(group):
            out.append((prev.string[prev.start() :].capitalize(), 1.0))
        else:
            out.append((prev.string[prev.start() : prev.end()].capitalize(), float(group[pos:])))
        return out

    def merge_same(self):
        elements = OrderedDict({})
        for ele, amount in self:
            if ele in elements:
                elements[ele] += amount
            else:
                elements[ele] = amount
        self[:] = [items for items in elements.items() if items[1] != 0]
        if self._do_sort:
            self.sort()

    def __str__(self):
        output = ""
        for element, number in self:
            if number == 1.0:
                output += element
            elif number.is_integer():
                output += element + str(int(number))
            else:
                output += element + str(number)
        return output

    def __contains__(self, item):
        # check if an element is in the formula
        return item in [el[0] for el in self]

    def index(self, item, **kwargs):
        return [el[0] for el in self].index(item, **kwargs)

    def __add__(self, other):
        out = Formula(self[:] + other[:], sort=self._do_sort)
        out.merge_same()
        return out

    def __sub__(self, other):
        sother = -1 * other
        out = Formula(self[:] + sother[:], sort=self._do_sort)
        out.merge_same()
        return out

    def __mul__(self, other):
        return Formula([(el[0], other * el[1]) for el in self], sort=self._do_sort)

    def __rmul__(self, other):
        return self * other
