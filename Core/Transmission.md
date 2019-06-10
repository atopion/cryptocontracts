# Structure of one entry #

```
    1. Previous Hash
    2. timestamp of creation
    3. List of public keys of the contract's parties
    4. raw hash value of the contract
    5. hash value signed by all parties
    6. sha-3 hash of point 1 - 5 (the previous hash for the next transaction) signed with all keys
```