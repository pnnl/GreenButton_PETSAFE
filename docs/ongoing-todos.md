[Priority] Working problems:
- [1] Max/min not yet implemented; theoretically possible, but the method is more complex than adding or multiplying.
    - Most promising: EvalMinSchemeSwitching() and EvalMaxSchemeSwitching(): https://openfhe-development.readthedocs.io/en/latest/api/classlbcrypto_1_1SWITCHCKKSRNS.html
    - Started testing- does not appear to work with threshold encryption, as it requires a private key that doesn’t exist for threshold contexts.
    - https://github.com/openfheorg/openfhe-development/blob/v1.1.2/src/pke/examples/scheme-switching.cpp#L875 for C++ example of usage; Python interface does have the needed functions, but the scheme-switching requirements remain a problem in threshold contexts.
    - Consider bitwise approach: X - Y positive or negative? Checking the sign bit.
        - Only holds if homomorphism keeps relative position: Enc(A) > Enc(B) when A > B may not hold true. Need to research + test.
        - Wasn't there a sign-getter function? Check. (Nope, just a negation function)
        - How do Zero Knowledge Proofs do it for cryptocurrency (you have greater than X funds)? That might be worth looking at.

- [2] Detecting outages (0s)
    - If X + X = X, then X is 0? Are there exceptions? Does this hold when encrypted, or does the nonce prevent this reliably (it should, but needs testing to be sure- unsure on CKKS nonce implementation)?
    - Same for X / X, X**2, etc.
    - If </> work: if not x > 0 and not x < 0, then x must = 0

- [3] Saving encrypted buildings and keys to file
    - OpenFHE objects will not serialize; no obvious methods to retrieve a pickle-able version in documentation
    - This also disallows multiprocessing and multithreading for encrypted data (relies on serializing code + objs)
    - Can retrieve key tags, but not *keys*. Still looking for possible methods to enable this.
    - Maybe pickle is the wrong approach here. SQLite?

- [4] Rename DCT config options to make more sense / be less confusing when looked at together.

- [5] Graph DCT coefficients at 15min resolution.
    - One line per day, 96 points per line.
    - Overlay 365 lines (one per day) on a graph for each building.
    - Make it a box plot so it's comprehensible.
