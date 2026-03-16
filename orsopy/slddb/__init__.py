"""
Package for a database of Scattering Length Density data (SLD) for neutron
and x-ray scattering.
The query to the DB includes recalculation of SLD for needed radiation.

Part of ORSO initiative, see: https://www.reflectometry.org/

Contributers:
    Artur Glavic <artur.glavic@psi.ch>
"""

try:
    from .database import SLDDB
    from .dbconfig import DB_FILE
    from .webapi import SLD_API
except ModuleNotFoundError:
    pass
else:
    api = SLD_API()
