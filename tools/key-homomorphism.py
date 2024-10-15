from lightphe import LightPHE
from lightphe.elliptic.Weierstrass import Weierstrass

ALGORITHM = "EllipticCurve-ElGamal"
#ALGORITHM = "ElGamal"
KEY_LENGTH = 521

# Conclusion: ECC Eg-Gamal is likely NOT homomorphic in respect to keys

keys_a = LightPHE(algorithm_name=ALGORITHM, key_size=KEY_LENGTH)
keys_b = LightPHE(algorithm_name=ALGORITHM, key_size=KEY_LENGTH)
keys_ab = LightPHE(algorithm_name=ALGORITHM, key_size=KEY_LENGTH) # Placeholder

message_a = 10
message_b = 5

match ALGORITHM:
    case "ElGamal":
        # Get the keys
        key_a_private = keys_a.cs.keys["private_key"]["x"]
        key_b_private = keys_b.cs.keys["private_key"]["x"]
        key_a_public = keys_a.cs.keys["public_key"]
        key_b_public = keys_a.cs.keys["public_key"]
        # Adjust keys
        key_ab_private = key_a_private + key_b_private
        key_ab_public = {"p": key_a_public["p"] + key_b_public["p"], "g": key_a_public["g"] + key_b_public["g"], "y": key_a_public["y"] + key_b_public["y"]}
        # Set keys
        keys_ab.cs.keys["private_key"]["x"] = key_ab_private
        keys_ab.cs.keys["public_key"] = key_ab_public

    case "EllipticCurve-ElGamal":
        # Get the keys
        key_a_private = keys_a.cs.keys["private_key"]["ka"]
        key_b_private = keys_a.cs.keys["private_key"]["ka"]
        key_a_public = keys_a.cs.keys["public_key"]["Qa"]
        key_b_public = keys_a.cs.keys["public_key"]["Qa"]
        # Adjust keys
        #key_ab_private = key_a_private + key_b_private
        # ECC uses public keys on an elliptic curve; addition should be done on that curve
        curve = Weierstrass()
        p = curve.p
        key_ab_public = curve.add_points(key_a_public, key_b_public, p=p)
        # Set keys
        #keys_ab.cs.keys["private_key"]["ka"] = key_ab_private
        keys_ab.cs.keys["public_key"]["Qa"] = key_ab_public

print("Message A:", message_a)
print("Message B:", message_b)

cipher_a = keys_a.encrypt(message_a)
cipher_b = keys_b.encrypt(message_b)

match ALGORITHM:
    case "ElGamal":
        cipher_ab = cipher_a * cipher_b
        print("Cipher A * B:", cipher_ab)
        cipher_ab = keys_ab.regenerate_ciphertext(cipher_ab)
    case "EllipticCurve-ElGamal":
        cipher_ab = cipher_a + cipher_b
        print("Cipher A + B:", cipher_ab)

message_ab = keys_ab.decrypt(cipher_ab)
print("Message AB:", message_ab)

# ECC ElGamal
# Library writeup: https://sefiks.com/2018/08/21/elliptic-curve-elgamal-encryption/
# Secret key is random x bits
# Public key is secret key * base point
# Base point is G = (55066263022277343669578718895168534326250603453777594175500187360389116729240, 
# 32670510020758816978083085130507043184471273380659243275938904335757337482424)
# Modulus is p = pow(2, 256) - pow(2, 32) - pow(2, 9) - pow(2, 8) - pow(2, 7) - pow(2, 6) - pow(2, 4) - pow(2, 0)
 
