---
layout: page  
title: "ORSO - file formats - draft and rules for the text reflectivity file"  
author: "Jochen Stahn"  
---

This document is based on discussions at various ORSO workshops and meetings. The main
contributors are: 
Andrew Caruana, 
Andrew McCluskey,
Andrew Nelson,
Artur Galvic,
Brian Maranville,
Bridget Murphy,
Maximilian Skoda, 
Joachim Wuttke,
Jochen Stahn,
Jos Cooper
and
Tim Snow.

The rules and examples given below are still under discussion and the header entries
listed are not exhaustive. Comments and contributions are welcome and should be 
communicated to <Jochen.Stahn@psi.ch>.

last modified: 2021-06-17

---

## some specifications

### file extension

It is recommended to use the suffix `.ort` (**o**rso **r**eflectivity **t**extfile) for
reflectivity files following this standard.

### placeholders

If there is no entry available for a keyword, the default value for both, string and numbers is
the string `null` 


### language

In line with CANSAS and NEXUS, we use American English for the key words. 
E.g. `polarization` rather than `polarisation`. 


### encoding

The text representation allows for ASCII characters following the !!! endcoding. 

For the keywords only !!! encoding is allowed. 


### date and time format

ISO8601 format for date and time: yyyy-mm-ddThh:mm:ss.
This is local time.
Do not use UTC (hence no suffix Z).
If the time zone shall be specified (e.g. for disambiguation of summer/winter time),
then append the UTC time offset in the form "+09:30".


### units

In the header, physical quantities shall always be stored with magnitude and unit in the form

    <quantity>:
         magnitude: <magnitude>
         unit: <unit>

Rules for using units:

- only ASCII symbols are to be used;
  - the greek letter μ is written as `mu` (e.g. `mum` for micrometer);
  - `angstrom` cannot be abbreviated (Å is not allowed, A stands for Ampere);
- composition with `*` and `/`, exponentiation with `**`
  - reciprocal units are written e.g. as `1/nm` for wavenumbers, `1/angstrom**2` for the scattering length density

Recommended units include:
- for angles, `rad`, `deg`;
- for lengths, `m`, `mm`, `nm`, `angstrom`;
- for durations, `s`;
- for energies, `eV`, `keV`;
- for temperatures, `K`.


### comments

There are 2 kinds of comments possible:

The key word `comment:` allows to add free text, e.g. to describe a related entry
in more detail.

A hash (`#`) declares everything that follows on the same line to be outside the
hirarchical structure and will be ignored by YAML (or JSON) based information
processing. E.g. the first line of the text representation contains information
not structured due to YAML rules and thus starts with `# # `, where the first
hash means *header* and the second *non-YAML entry*.

---


## the header

The header may contain more sections than presented below - and also the sections may
contain user-defined `key: <value>` pairs on all levels. These of course should not
interfere with defined content, and the rules for units and formats should be applied as
stated here.

The header follows a hierarchical structure and is formatted according to YAML (se below) 
or JSON rules. In addition, each line of the header starts with a hash and a space `# `
(wrapped YAML), which is the default header marker in Python (and other languages).


### first line

The first line contains information about

- the general content;
- the ORSO file format version (and level of strictness) used;
- the encoding;
- a link to us.

Since it is not part of the YAML hirarchy, a second hash is needed.

    # # ORSO reflectivity data file | 0.1 standard | YAML encoding | https://www.reflectometry.org/`  

### second line

optional, recommended

This (comment) line should help the user to identify the content based on a few key words.
It is free format and no further rules apply.

    # # <title> | <date> | <sample name> | <what>
    
e.g.

    # # Interdiffusion in Fe | 2020-12-24 | sample fe-457-2 | R(q_z)

### data source

mandatory

This section contains information about the origin and ownership of the raw data, 
together with details !!!

    # data_source:             This information should be available from the raw data 
                             file. If not, one has to find ways to provide it.  

    #     owner:               This refers to the actual owner of the data set, i.e.
                             the main proposer or the person doing the measurement
                             on a lab reflectometer
    #         name:            main proposer at large scale facility or experimentator at
                             lab source
    #         affiliation:     
    #         email:           optional  
    #     experiment:  
    #         facility:
    #         proposalID:           proposal ID
    #         doi:
    #         timestamp:         yyyy-mm-ddThh:mm:ss 
    #         title:        proposal or project title
    #         instrument:   
    #         probe:        neutrons or x-rays
    #     sample:  
    #         identifier:   mandatory, string
    #         type:         best effort, solid/liquid, liquid/solid, gas/liquid, liquid/liquid, solid/gas, gas/solid 
    #         composition:  optional 
                            free text notes on the nominal composition of the sample  
                            e.g. Si | SiO2 (20 A) | Fe (200 A) | air (beam side)
    #         description:  optional, free text
    #         environment:  optional, free text, name of the sample environment device(s)

The following list of sample parameters is incomplete and expandable

    #         temperature:
    #             unit:
    #             value:
    #             min: 
    #             max:

In case there are several temperatures:

    #           - description:
    #             unit:
    #             value:
    #             min:
    #             max:
    #           - description:
    #             unit:
    #             value:
    #             min:
    #             max:

    #         magnetic_field:
    #             unit:
    #             value:
    #             direction: 
    #         electric_field:
    #             unit:
    #             value:
    #         electric_current:
    #             unit:
    #             value:
    #         electic_ac_field: 
    #             amplitude:
    #                 unit:
    #                 value:
    #             frequency: 
    #                 unit:
    #                 value:


    #    measurement: mandatory 
    #         scheme:  optionl, best practice
                       angle-dispersive / energy-dispersive / angle- and energy-dispersive 
    #         instrument_settings:  
    #             configuration: half / full polarised | liqid_surface | ....   free text
    #             incident_angle:  
    #                 unit:        
    #                 value:
    #                 min:  
    #                 max:   
    #             wavelength:
    #                 unit:       
    #                 value:
    #                 min: 
    #                 max: 
    #             polarization: 

For neutrons one of `p / m / pp / pm / mp / mm  / vector`

For x-rays one of `tba`   

    #         data_files:  
    #             - file:       mandatory, free text (file name or identifier doi)
    #               timestamp:  yyyy-mm-ddThh:mm:ss
    #             - file:       
    #               timestamp:  
    #         reference_data_file:  
    #             - file:   
    #               timestamp: 
  
  
### data reduction

This section is mandatory whenever some kind of data reduction was performed. 

An example where it is not required is the output of an x-ray lab source, as 
long as no normalisation or absorber correction has been performed.

The content of this section should contain enough information to rerun
the reduction, either by explicitely hosing all the required information,
or by refering to a nexus representation, a note book or a log file. 

    # reduction:  
    #      software:
    #          name:         name of the reduction software
    #          version:      its version 
    #          platform:     operating system
    #      computer:         optional, computer name
    #      call:             if applicable, command line call or similar               best practice
    #      script:           path to e.g. notebook
    #      binary:           path to full information file
    #      timestamp:        date and time of file creation,

The following subsection identifies the person or routine who created this file.
She/he is the one responsible for the content.

    #      creator:         
    #          name:         
    #          affiliation:   
    #          email:       optional

Optional, but recommended is a list of corrections performed in free text.
This helps the user to set the respective parameters for the data analysis.

In case a correction step follows a certain published algorithm, a link
to the publication or homepage might be given.

This part might be expanded by defined entries, which are understood by
data analysis software.

    #      corrections:          free text to inform user
    #         - footprint doi
    #         - background
    #         - polarisation
    #         - ballistic correction
    #         - incident intensity
    #         - detector efficiency 
    #         - scaling / normalisation
    #      comment: |
    #         Normalisation performed with a reference sample            

The `comment` is used to give some more information. 

### column description

This data representation is essentially ment to store a physical observable *I*
as a function of a variable *x*. Together with the related information about
the error of *I* and the resolution of *x* this leads to the defined leading 4 
columns of the data set. I.e.

1. *x*   with units
2. *I*   with units (if applicable)
3. *sigma* of *I*   with units (if applicable)
4. *sigma* of resolution of *x*   with units 

where for columns 3 and 4, *sigma* is the standard deviation of a Gaussian
distribution.

The exampe given refers to *R(Qz)* which has unit 1

    # column_description:
    #      - name:        Qz
    #        unit:        1/angstrom 
    #        description: wavevector transfer
    #      - name:        R
    #        description: reflectivity
    #      - name:        sR 
    #        description: standard deviation of reflectivity
    #      - name:        sQz
    #        unit:        1/angstrom 
    #        description: standard deviation of wavevector transfer resolution

Further columns can be of any type, content and order. But always with
description and units. E.g.

    #     - name:        alpha_i
    #       unit:        deg  
    #       description: angle of incidence
    #     - name:        lambda
    #       unit:        angstrom 
    #       description: wavelength

In case there are various data sets in one file, the first one can be given an identifier
with the optional line

    # data set: <identifier>

Also optionally there might be a short-notation column description preceded with
a hash, since this line is outside the YAML structure

    # #         Qz             RQz              sR              sQ

---

## data set

The data set is organised as a rectangular array, where all entries in a column have the
same physical meaning. The leading 4 columns strictly have to follow the rules stated
in the *column description* section.

- All entries have to be of the same data type, preferably float.
- There is no leading space.
- Separators are spaces, tabs are not allowd.

- It is recommended to use the same format for all columns,
  preferably `%16.9e`.

```
1.03563296e-02  3.88100068e+00  4.33909068e+00  5.17816478e-05
1.06717294e-02  1.16430511e+01  8.89252719e+00  5.33586471e-05
...
```

## multiple data sets

In case there are several data sets in one file, e.g. for different spin states or temperatures, 
the following rules apply:

### separator

Optionally, the beginning of a new data set is marked by an empty line.
This is recognised by gnuplot as a separator for 3 dimensional data sets.

The mandatory separator between data sets is the string

    # data set: <identifier>

where <identifier> is either an unique name or a number. The default numbering of dats sets starts with 0, the first additional one thus gets number 1 and so on.

### overwrite meta data

Below the separator line, meta data might be added. These overwrite the meta data supplied in the header 
(i.e. data set 2 does not know anything about the changes made for data set 1).


For the case of additional input data with different spin state this might look like

    #     data_source:
    #         measurement:
    #             polarisation: -
    #     reduction:
    #         input_files:
    #             data_files:
    #                 - file     : amor2020n001930.hdf
    #                   created  : 2020-02-03T15:27:45


### repetition of short-version column description

optional

    # #         Qz             RQz              sR              sQ          lambda

### next data set

The following data set has to be of the same format (number, format and description of columns) as data set 0,
probably with a different number of rows.

```
1.03563296e-02  1.08100068e+00  4.33909068e+00  5.17816478e-05  4.00000000e+00
1.06717294e-02  1.06430511e+01  8.89252719e+00  5.33586471e-05  4.10000000e+00
...
```

---

## the end

There are no rules yet for a footer. Thus creating one might collide with future versions of the ORSO (.ort) format.
