from openfhe import *
from typing import Optional
from config import BATCH_SIZE
# Value obtained from print(str(logging.ERROR))

class Decryptor:
    def __init__(
            self,
            keys: list, # List of keys to decrypt with
            cc, # CC object from openfhe; needs evalkeys
            order: list, # Order of meters for decryption
            #key_location: Optional[str] = "./keys/", # location of keys, dir path
            batch_size: Optional[int] = 1,
            length: Optional[int] = 2 # Number of values in a vector
    ):
        # Add any missing slashes to the key location, then read the keys from file
        #if key_location[-1] != "/":
        #    key_location += "/"
        try:
            self.__cc = cc
            self.__keys = keys
            self.__meter_order = order
            self.__batch_size = batch_size
            self.__length = length
        except:
            print("Keys not found or algorithm incorrect.")

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
        #try:
            # The usual format when reading file with pandas
            #if isinstance(target, str):
            #    target = self.__format_for_decrypt(target)
            # Re-init ciphertext if needed
            #if isinstance(target, tuple):
            #    target = self.__re_initialize(target)
            #elif not isinstance(target, object):
            #    pass
            #else:
            #    print("Cannot decrypt: input type not string, nested tuple, or ciphertext.")
            #    return target
            # Only decrypt once ciphertext is initialized
            partial_decryptions = []
            print("Meter order:", self.__meter_order)
            for meter in self.__meter_order:
                key = self.__keys[meter]
                if meter == self.__meter_order[0]:
                    print("Leader meter", meter, "decrypting.")
                    partial_decryptions += self.__cc.MultipartyDecryptLead([target], key.secretKey)
                else:
                    print("Follower meter", meter, "decrypting.")
                    partial_decryptions += self.__cc.MultipartyDecryptMain([target], key.secretKey)
                print("Fusing partial decryptions.")
            plaintext = self.__cc.MultipartyDecryptFusion(partial_decryptions)
            #plaintext.SetLength(BATCH_SIZE) # TODO: set using batch size? or have it passed in? or 1?
            plaintext.SetLength(self.__length)
            return plaintext
        #except AttributeError:
            # Came up when trying to decrypt non-encrypted data
            # TODO: return the data instead so everything still works
            #print("Could not decrypt. Are you passing unencrypted data?")
            #return target
        #except Exception as error:
            #print("Decryption failed:", error)
            #return target

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