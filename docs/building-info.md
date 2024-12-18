# Creation Notes
- Sites were accepted if 90% of data was present between 2023-01-01 and 2023-12-31.
- Size range requested was 2-10 units per building.
- Buildings created using data from 2023.
- Time resolution of buildings' data: every 15 minutes.
- Time taken to create all:  1029.1598472640035 seconds
- Average time to create one building for this set: 102.91598472640035 seconds

## Building 0
- Size: 2
- Sites (point_id): 33789, 33387

## Building 1
- Size: 8
- Sites (point_id): 25291, 51837, 27163, 26422, 47732, 27152, 26202

## Building 2
- Size: 2
- Sites (point_id): 25924, 25861

## Building 3
- Size: 2
- Sites (point_id): 47612, 50838
- Noticeable oddity: DCT average greater than actual data

## Building 4
- Size: 7
- Sites (point_id):47684, 25855, 25367, 36468, 47777, 33354, 35882

## Building 5
- Size: 2
- Sites (point_id): 25394, 26863

## Building 6
- Size: 5
- Sites (point_id): 26961, 25367, 26727, 33342, 25400

## Building 7
- Size: 2
- Sites (point_id): 25823, 47684

## Building 8
- Size: 3
- Sites (point_id): 52753, 26444, 34696

## Building 9
- Size: 2
- Sites (point_id): 25479, 26454

---

# DCT Coefficient Reduction Methods Overview

## Drop Top %

These graphs show one actual demand curve alongside a "smoothed" version created by performing DCT on the curve, setting a percentage of the coefficients that correspond to high frequencies equal to 0, then reconstructing the data from the modified coefficients.

**Example (with fake values):** 
If this is the coefficient set after DCT:
[2.7, 6, 0.5, 63, 9, 12, 2, 8]

Applying this method with a value of 0.5 (drop top 50%) yields the following:
[2.7, 6, 0.5, 63, 0, 0, 0, 0]

## Drop Top %, Keep Largest N

These graphs show one actual demand curve alongside a "smoothed" version created by performing DCT on the curve, setting a percentage of the coefficients that correspond to high frequencies equal to 0 EXCEPT for the largest N coefficients in that range, then reconstructing the data from the modified coefficients.

**Example (with fake values):** 
If this is the coefficient set after DCT:
[2.7, 6, 0.5, 63, 9, 12, 2, 8]

Applying this method with values of 0.5 and 1 (drop top 50%, keep 1 top value) yields the following:
[2.7, 6, 0.5, 63, 0, 12, 0, 0]

## Drop Below Threshold

These graphs show one actual demand curve alongside a "smoothed" version created by performing DCT on the curve, setting all coefficients below a certain threshold to 0, then reconstructing the data from the modified coefficients.

**Example (with fake values):** 
If this is the coefficient set after DCT:
[2.7, 6, 0.5, 63, 9, 12, 2, 8]

Applying this method with a value of 10 (drop all coefficients less than 10) yields the following:
[0, 0, 0, 63, 0, 12, 0, 0]

---

# RMSE values

## Lowpass on DCT averages: drop 25%
- 5 days (no weekend, July): 0.0016161245939171058
- 7 days (July): 0.0011440969543148735
- 2 weeks (July): 0.0007718909406780103
- 1 month (Jan): 0.001311796785600896
- 1 month (Apr): 0.0010053388964150875
- 1 month (Jul): 0.0005858792817529471
- 1 month (Sept): 0.0007284344372757196
- Jan-Mar: 0.000765684656299793
- Apr-Jun: 0.000471363399405233
- July-Sept: 0.00042508670972608696
- Oct-Dec: 0.0005148838391364932
- 1 year: 0.0002914878063411965

## Lowpass on DCT averages: drop 50%
- 5 days (no weekend, July): 0.002531705248436403
- 7 days (July): 0.002040940092964838
- 2 weeks (July): 0.0012814899409069936
- 1 month (Jan): 0.00187109733410543
- 1 month (Apr): 0.0015602507369039847
- 1 month (Jul): 0.0010605792862025708
- 1 month (Sept): 0.0010953741217454523
- Jan-Mar: 0.0011981160343847985
- Apr-Jun: 0.0006698193901671464
- July-Sept: 0.0006530183413742525
- Oct-Dec:  0.0007224677899963142
- 1 year: 0.00044836808279666415

## Lowpass on DCT averages: drop 75%
- 5 days (no weekend, July): 0.003602374129148282
- 7 days (July): 0.0030939440952774
- 2 weeks (July): 0.002124679502381904
- 1 month (Jan): 0.002741160225712968
- 1 month (Apr): 0.0025096405712424852
- 1 month (Jul): 0.0015161899156552092
- 1 month (Sept): 0.0014484509375231823
- Jan-Mar: 0.0016195685498386417
- Apr-Jun: 0.0012689900711329973
- July-Sept: 0.000910862435167422
- Oct-Dec: 0.001142181366921209
- 1 year: 0.0006790400418626871

## Lowpass on DCT averages: drop 90%
- 5 days (no weekend, July): 0.0050010623632438436
- 7 days (July): 0.004320998594714824
- 2 weeks (July): 0.0035128106244574006
- 1 month (Jan): 0.005014160377927581
- 1 month (Apr): 0.005784093068698587
- 1 month (Jul): 0.0030698840011824198
- 1 month (Sept): 0.0030108775489703856
- Jan-Mar: 0.0031028190729588583
- Apr-Jun: 0.003910237683975878
- July-Sept: 0.0024287168405623775
- Oct-Dec: 0.002152703473643442
- 1 year: 0.0022263792092912056

## Lowpass on DCT averages: drop 95%
- 5 days (no weekend, July): 0.006070686476702608
- 7 days (July): 0.005574785404050756
- 2 weeks (July): 0.004394998665231048
- 1 month (Jan): 0.007881095849035753
- 1 month (Apr): 0.009568539996086296
- 1 month (Jul): 0.004022444093929262
- 1 month (Sept): 0.004958489766493014
- Jan-Mar: 0.0055422955458974766
- Apr-Jun: 0.006918366081403005
- July-Sept: 0.0037389575666458815
- Oct-Dec: 0.004507223687693352
- 1 year: 0.004386979285352201

## Lowpass on DCT averages: drop 96.5%
- 5 days (no weekend, July): 0.00613065893704836
- 7 days (July): 0.005639354169163078
- 2 weeks (July): 0.004653566492813472
- 1 month (Jan): 0.0201833510942002
- 1 month (Apr): 0.012740192102266368
- 1 month (Jul): 0.004527793170843731
- 1 month (Sept): 0.006528791942940551
- Jan-Mar: 0.01882958544549359
- Apr-Jun: 0.008851405699796044
- July-Sept: 0.004697106156122659
- Oct-Dec: 0.01093446545476663
- 1 year: 0.010439642167631194

## Lowpass on DCT averages: drop 98%
- 5 days (no weekend, July): 0.017921579810945686
- 7 days (July): 0.01671849200167531
- 2 weeks (July): 0.015397926253015476
- 1 month (Jan): 0.02698846984429197
- 1 month (Apr): 0.021348299720756237
- 1 month (Jul): 0.015471576240971568
- 1 month (Sept): 0.010974733173457294
- Jan-Mar: 0.027094383108882264
- Apr-Jun: 0.014401480338749568
- July-Sept: 0.012882907255188305
- Oct-Dec: 0.016162652168712117
- 1 year: 0.015883968186424385

---