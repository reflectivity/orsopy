=======
History
=======

1.2.1 (2024-07-01)
------------------

* Add full compatibility with standard Python dataclasses.
* Add scripts to convert text to binary format and back (orsopy.ort2orb and orsopy.orb2ort).
* Multiple updates to documentation.
* Fix column header line for multi-dataset files written wrongly #128.
* Fix some issues with validation and schema generation.
* Fix bug in NeXus file writer for certain header configurations.

1.2.0 (2024-02-23)
------------------

* Introduce reading and writing of NeXus files ORSO binary standard (*.orb)
* Add some extra attributes from updated ORSO specification (v1.1).
* Add polarization options for x-ray instruments.
* Fix compatibility with Python 3.12, resolving issue #115.
* Move tests to orsopy sub-folders to prevent interference with other packages.
* Some updates to the package documentation.
* Fix some cases where numpy based scalars where not properly converted to YAML.

1.1.0 (2023-02-20)
------------------

* Introduction of simple model language that can be used to describe
  sample structures. The module *orsopy.fileio.model_language* is used to implement
  and parse the model language.
  See https://www.reflectometry.org/projects/simple_model for specifications.
  Sample model examples can be found in the examples folder together
  with scripts using the orsopy module to parse and plot the data.
* Add polarization channels for x-ray experiments
* Implement ErrorValue class for optional description of errors
  on values within the file header.
* Update of .ort standard according to discussions with community.
  (E.g. rename of column attribute "dimension" to "physical_quantity")

1.0.1 (2022-06-28)
------------------

* Fix bug that did allow some dictionary type values to be created in Sample.
* Update the schema files for released .ort standard.
* Sample.sample_parameters keys to be strings and values restricted to
  Value, ValueRange, ValueVector or ComplexValue.
* Add *as_unit* method to value classes that uses the *pint* library to convert
  values to supplied unit automatically.

1.0.0 (2022-06-10)
------------------

* ORSO general assembly has voted to release the first version of orsopy together with the
  text representation of the text file (.ort) specification.
  See https://www.reflectometry.org/workshops/workshop_2022/

0.1.1 (2022-06-08)
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
