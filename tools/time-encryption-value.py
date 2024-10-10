from time import perf_counter
from random import randrange
from lightphe import LightPHE
from os.path import exists

TEST_COUNT = 10000
decimal_places = 8 # How many decimal places to keep; needs to be the same when decrypted
CONVERSION_SCALAR = 10**decimal_places

total_time = 0

def setup_encryption():
    ALGORITHM = "EllipticCurve-ElGamal"
    KEY_LENGTH = 521
    KEY_LOCATION = "../keys/"
    # Make and export keys
    try:
        if "keys" not in globals() and not exists(KEY_LOCATION + "public.txt"):
            keys = LightPHE(algorithm_name = ALGORITHM, key_size = KEY_LENGTH)
            try:
                keys.export_keys(target_file = KEY_LOCATION + "public.txt", public = True)
                keys.export_keys(target_file = KEY_LOCATION + "private.txt", public = False)
            except Exception as ex:
                print("Unable to export keys. Decryption may fail. Reason: " + str(ex))
            return keys
        elif exists(KEY_LOCATION + "private.txt"):
            privkey = LightPHE(algorithm_name=ALGORITHM, key_file=KEY_LOCATION + "private.txt")
            return privkey
        else:
            print("Encryption setup failed.")
            raise SystemExit
    except:
        print("Key generation failure. Aborting.")
        raise SystemExit


keys = setup_encryption()

max = 0
min = 10000

for i in range(0, TEST_COUNT):
    if i % 500 == 0:
        print("Progress:", i, "/", TEST_COUNT)
    value = randrange(-5, 5)
    start = perf_counter()
    encr_value = keys.encrypt(int(float(value) * CONVERSION_SCALAR))
    end = perf_counter()
    time_taken = end - start
    total_time += time_taken
    if time_taken > max:
        max = time_taken
    elif time_taken < min and time_taken != 0:
        min = time_taken

avg_time = total_time / TEST_COUNT
print("Average time to encrypt one record:", avg_time)
print("Best time:", min)
print("Worst time:", max)