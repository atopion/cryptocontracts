# Core functions #

## Description ##

This document provides a documentation and explanation about the core functions files located in this directory.
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
    Core.checksum(path=None, s=None, bytes=None)
Produces the checksum from a given file, string or bytearray. Algorithm: `whirlpool, keccak and blake`

#### Parameters: ####

    path:  path to the file to produce the checksum from.
    s:     String to produce the checksum from.
    bytes: byte array to produce the checksum from.

#### Returns: ####

an integer which is the checksum of the given data or a random number if no data is given. If two or more arguments are given, the checksum of the first given argument is returned.\
If the ```path``` argument is given but the referenced file could not be found (e.g. file does not exists or is a directory) ```-1``` is returned.

---

### Method: Core.compare ###
    Core.compare(checksum_a, checksum_b)
Compares the two checksums for equality.

#### Parameters: ####

    checksum_a: The first checksum as produced by Core.checksum()
    checksum_b: The second checksum as produced by Core.checksum()

#### Returns: ####
`1` if checksum_a and checksum_b are given and equal, `0` otherwise.

---

### Method: Core.lookup ###
    Core.lookup(checksum)
Looks up a specific checksum in the blockchain for validation.

#### Parameters: ####

    checksum: The checksum to look up.

#### Returns: ####
A Transmission object containing the existing transmission from the blockchain if it exists, `None` otherwise.

---

### Method: Core.produceTransmission ###
    Core.produceTransmission(previous_hash, pub_keys, document_hash)
Produces a new Transmission Object containing the given objects.

#### Parameters: ####
    
    previous_hash: String containing the hash of Transmission this Transmission should be attached after.
    pub_keys:      List of Public Keys from all parties signing the document.
    document_hash: String containing the hash of the document, produced by Core.checksum
    
#### Returns: ####
A newly produced Transmission object containing the given parameters and the ones directly derived from them or `None` if any parameter is missing.

---

### Method: Core.verifyTransmission ###
    Core.verifyTransmission(transmission)
Verifies a Transmission object by testing:

- Are all parameters set?
- Does the transmission hash belong to this transmission?
- Were the given public keys used to sign the document hash?
- Were the given public keys used to sign the transmission hash?
- Do the given public keys exist in the registry and are not the same?

#### Parameters: ####

    transmission: The transmission object to verify
    
#### Returns: ####
`1` if the transmission is not `None` and passes all test as above, `0` otherwise.

---

## Class Transmission ##
The class Transmission encapsulates the data and production methods for a transmission.

### Parameters: ###
    - previous_hash:     Hash value of the previous Transmission
    - timestamp:         The timestamp of creation, used for sorting
    - pub_keys:          List of public keys from the signing parties
    - hash:              Hash value of the document, produced by Core.checksum()
    - signed_hash:       Hash value of the document, signed with all public keys
    - transmission_hash: Hash value of the other parameters of the Transmission, signed with all public keys

---

### Method: sign_self ###
    Transmission.sign_self()
Produces the transmission hash and signs it with the public key list.

---

### Method: check_self ###
    Transmission.check_self()
Checks whether the transmission_hash value is correct.

#### Returns: ####
`True` if the transmission_hash value can be reconstructed by the other parameters of the object, `False` otherwise.

---

### Method: is_valid ###
    Transmission.is_valid()
Checks whether all parameters are set and not `""`.

#### Returns: ####
`True` if all paramters are set and not `""`, `False` otherwise.

---

### Method: compare ###
    Transmission.compare(transmission)
Compares the object with another transmission.

#### Parameters: ####
    transmission: another Transmission object to compare to.
    
#### Returns: ####
`True` if the two transmissions are equal, `False` otherwise.

---

### Method: to_json ###
    Transmission.to_json()
Returns the current object as a json string.

#### Returns: ####
The current object as a json string.

---

### Method: from_json ###
    Transmission.from_json(json_str)
Creates a new Transmission object from the given json string.

#### Parameters: ####
    json_str: The json string containing the object.
    
#### Returns: ####
A new Transmission object.

---

## Class Signing ##
Currently only a dummy implementation. To be used for signing and unsigning data.

### Method: sign ###
    Signing.sign(value, keys)
    
---

### Method: unsign ###
    Signing.unsing(value, keys)

---

## Class Client ##
Currently only a dummy implementation. To encapsulate the client behavior of a node in the network.

### Method: place_transmission ###
Attempts to place a transmission in the network.

#### Parameters: ####
    - pub_keys: List of public keys of parties in the document.
    - document_hash: the document checksum as a string.
    
---