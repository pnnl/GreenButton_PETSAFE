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

---

## DCT averaged, then reconstructed for time period

### Process:
- Calculate DCT on every day within a time period.
- Average values for each coefficient; sum all values for coefficient, divide by number of days
- Reconstruct data from resulting average DCT coefficients

### Notes:
- For one year, poorly tracks patterns within a day; does show some notable trends, but only weakly
- For 5-6 months, shows patterns better; reappearance of smaller peaks, slightly stronger tracking of demand
- For 3 months, patterns noticeably present. Suggestive of seasonal changes affecting year-resolution daily average?
- For one month, patterns noticeably present; still "softened" from original data, but jagged and shows trends for month's days
