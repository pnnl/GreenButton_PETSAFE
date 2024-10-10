# Performance

## Limitations and Details
- All buildings created for the year of 2021 only.
- Seed used: 976616126
- Buildings created using seed: 10
- Size of buildings: 2-5 units
- Encryption algorithm: Elliptic Curve ElGamal, 521-bit, saved keys.

## Results

### Query times for all data available (5 years)
- 6 units (26444, 27168, 33342, 51837, 25838, 26836): ~90 mins
- 5 units:
- 4 units (35390, 33789, 25973, 25291): ~30 mins
- 3 units (26620, 59489, 47757); (26962, 33354, 51908): 5-10 mins, 22 w/encryption
- 2 units (35390, 33789): ~1-2 mins

### No encryption, one year of data
- Time to create 10 buildings: 382.36922200000845 seconds (6.37 minutes)
- Another run of 10 on a different seed: 123.93 seconds (2 minutes)
- Time to create statistics:
- Time to decrypt: N/A

### With encryption, one year of data
- Time to create the same 10 buildings: 1836.1158292000182 seconds (30.60 minutes)
- Time to create statistics:
- Time to decrypt:

### No encryption, one year, one building
- 5 units:
- 4 units:
- 3 units:
- 2 units:

### With encryption, one year, one building
- 5 units:
- 4 units:
- 3 units:
- 2 units:

# Accuracy
## Results

### No encryption
- Sum:
- Average:
- Max:
- Min:
- Outage periods:

### With encryption
- Sum:
- Average:
- Min: Not possible with Elliptic Curve ElGamal (may be possible with homomorphic DP? Testing needed.)
- Max: Not possible with Elliptic Curve ElGamal
- Outage periods: can be calculated IF a ciphertext of 0 is provided