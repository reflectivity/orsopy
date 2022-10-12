=====
Usage
=====

The easiest way to use :py:mod:`orsopy.fileio` (the module of :py:mod:`orsopy` that includes file reading and writing) to produce metadata-rich .ort reducted reflectometry files involves integrating this into your data reduction workflow.
Early in the workflow, the :py:mod:`orsopy.fileio` should be imported and an empty :code:`fileio.orso.Orso` header object. 

.. code-block:: python 

    from orsopy import fileio

    header = fileio.orso.Orso.empty()

Having created the empty header object we can start to populate the appropriate components of it. 
For example, if we want to identify the probing radiation as neutrons, we include this as follows. 

.. code-block:: python 

    header.data_source.experiment.probe = 'neutrons'

Full details of the different components that can be populated can be found in the `documentation`_ here or in the `file format specification`_.
Note that this specification includes information regarding the required and optional components to be included for a file to be considered a valid .ort file.
Having populated the metadata for the header, we then want to assign the data that we want to write (this will be after your data reduction has been performed).
This is achieved by producing a :code:`fileio.orso.OrsoDataset` object, which takes the header and the relevant data columns (below these are :code:`q`, :code:`R`, :code:`dR`, and :code:`dq`) as inputs. 

.. code-block:: python 

    dataset = fileio.orso.OrsoDataset(header, np.array([q, R, dR, dq]).T)

The dataset can then be saved with the following function, where :code:`'my_file.ort'` is the name for the file to be saved under. 

.. code-block:: python

    fileio.orso.save_orso([dataset], 'my_file.ort') 

Note that if you want to save more than one dataset in a single file, this can be achieved by including these in the list that is passed to this function. 


.. _`documentation`: ./modules.html#fileio
.. _`file format specification`: https://www.reflectometry.org/file_format/specification