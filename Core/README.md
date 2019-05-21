# Core functions #

## Description ##

This document provides a documentation and explaination about the core functions files located in this directory.
Purpose of these files is to have a single implementation of the GUIs core functions in one place, so that every GUI implementation can easily use them. The core functions are available in different programming languages, currently in:

`    - Python (core_functions.py) `<br>
`    - more to come `

The provided functions implement all basic interactions of the GUI with the blockchain, as well as the production, comparison and lookup of checksums and the signing of keys. Additionally, core functions implements a minimum working script, which is able to produce the checksum of a given file and upload it into the blockchain.



# Classes #

## Class Core ##
The class Core encapsulates all static and indepentent functions.\
Even though it is possible to define functions outside of a class in a couple of programming languages (e.g. Python), some supported languages require all functions to be inside of a class (e.g. Java). So, to keep the codebase uniform and to ease the translation to other languages, the Core class is used in all programming languages which support classes and static functions.

---

### Method: Core.checksum ###
    Core.checksum(path=None, bytes=None, str=None)
Produces the checksum from a given file or bytearray. Algorithm: tba

#### Parameters: ####

    path:  path to the file to produce the checksum from.
    bytes: byte array to produce the checksum from.
    str:   String to produce the checksum from.

#### Returns: ####

an integer which is the checksum of the given data or a random number if no data is given.

---

### Method: Core.compare ###
    Core.compare(checksum_a, checksum_b)
Compares the two checksums for equality.

#### Parameters: ####

    checksum_a: The first checksum as produced by Core.checksum()
    checksum_b: The second checksum as produced by Core.checksum()

#### Returns: ####
`1` if checksum_a and checksum_b are given and equal, `0` otherwise.