=======
History
=======

0.1.0 (2022-06-08)
------------------

* Fix missing data files in distribution

0.1.0 (2022-05-19)
------------------

* Revise .ort file header speicifcation according to ORSO discussions.
* Implement option for automatic unit conversion based on pint library
* Improve yaml export to support compact on-line layout for e.g. Value
* Add a ErrorColumn for clear separation between data and error columns
  and allow specification of type/distribution of error with conversion
  factors to get standard deviation (sigma)
* Add a ComplexValue class
* Fix some type conversions where e.g. lists have been converted to str

0.0.5 (2022-02-04)
------------------

* Merge the slddb package into orsopy for simple query of the database.
  SLD db will transition to orsopy for its backend.

0.0.4 (2022-01-19)
------------------

* Fix a bug prventing usage of fileio on python >=3.10.1 due to changes in dataclasses internal API
* Replace the metaclass implementation by a decorator behaving similar to dataclass
* Add meeting minutes documenting ORSO decisions
* Define documentation how to auto-format code and execute on source
* More documentation improvements

0.0.3 (2021-11-14)
------------------

* Implement user_data from custom keyword arguments
* Improvements to documentation
* Backport to python 3.6 and 3.7
* Allow user defined spaces between multiple datasets

0.0.2 (2021-10-08)
------------------

* Integration of PyPI with Github build system

0.0.1 (2021-10-08)
------------------

* First release on PyPI as alpha version.
