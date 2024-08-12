from lightphe import LightPHE
from os import environ
from typing import Optional
# Value obtained from print(str(logging.ERROR))
# LightPHE is a little log-happy and needs to be reminded not to spam
environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only

class Decryptor:
    def __init__(
            self,
            key_location: Optional[str] = "./keys/", # location of keys, dir path
            algorithm: Optional[str] = "EllipticCurve-ElGamal", # The encryption algorithm
            decimal_places: Optional[int] = 5 # the number of decimal places to adjust numbers by
    ):
        # Add any missing slashes to the key location, then read the keys from file
        if key_location[-1] != "/":
            key_location += "/"
        try:
            self.__keys = LightPHE(algorithm_name = algorithm, key_file=key_location + "private.txt")
        except:
            print("Keys not found or algorithm incorrect.")
        self.__scalar = 10**decimal_places

    # Converts from stored data back to ciphertext object to enable decryption.
    # Target is the data to re-init as ciphertext
    def __re_initialize(self, target):
        try:
            target = self.__keys.create_ciphertext_obj(target)
        except:
            print("Unable to re-initialize ciphertext.")
        return target

    # Decrypts a target using the Decryptor's algorithm argument
    # Target is the data to decrypt
    def decrypt_target(self, target):
        try:
            # The usual format when reading file with pandas
            if isinstance(target, str):
                target = self.__format_for_decrypt(target)
            # Re-init ciphertext if needed
            if isinstance(target, tuple):
                target = self.__re_initialize(target)
            elif not isinstance(target, object):
                print("Cannot decrypt: input type not string, nested tuple, or ciphertext.")
                return target
            # Only decrypt once ciphertext is initialized
            data = self.__keys.decrypt(target)
            # Fix the scaling
            data = float(data) / (self.__scalar)
            return data
        except AssertionError:
            # This came up with a too-short ciphertext at one point
            print("Cannot decrypt: key or ciphertext incorrect.")
            return target
        except AttributeError:
            # Came up when trying to decrypt non-encrypted data
            # TODO: return the data instead so everything still works
            print("Could not decrypt. Are you passing unencrypted data?")
        except Exception as error:
            print("Decryption failed:", error)
            return target

    # Data is read from files as a string like the following, where
    # w, x, y, and z are integers: "((w, x), (y, z))". This converts
    # the string back to the nested tuples that LightPHE expects.
    # Target is the string to convert back to tuples
    def __format_for_decrypt(self, target):
        try:
            items = target.split(",")
            clean_items = []
            for item in items:
                # Remove non-numbers
                cleaned_item = int("".join(c for c in item if c.isdigit()))
                clean_items.append(cleaned_item)
            del items
            inner_tuple_1 = (clean_items[0], clean_items[1])
            inner_tuple_2 = (clean_items[2], clean_items[3])
            output = (inner_tuple_1, inner_tuple_2)
        except Exception as error:
            print("Cannot format for decryption:", error)
        return output