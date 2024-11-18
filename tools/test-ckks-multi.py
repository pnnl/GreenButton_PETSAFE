from openfhe import *
from math import log2

def main():
    print("\n=================RUNNING FOR CKKSrns======================\n")
    RunCKKS()

def RunCKKS():
    batchSize = 16

    parameters = CCParamsCKKSRNS()
    parameters.SetMultiplicativeDepth(3)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(batchSize)

    cc = GenCryptoContext(parameters)
    # Enable features you wish to use
    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)
    cc.Enable(ADVANCEDSHE)
    cc.Enable(MULTIPARTY)

    ##########################################################
    # Set-up of parameters
    ##########################################################

    # Output the generated parameters
    print(f"p = {cc.GetPlaintextModulus()}")
    print(f"n = {cc.GetCyclotomicOrder()/2}")
    print(f"lo2 q = {log2(cc.GetModulus())}")

    ############################################################
    ## Perform Key Generation Operation
    ############################################################

    print("Running key generation (used for source data)...")

    # Round 1 (party A)

    print("Round 1 (party A) started.")

    kp1 = cc.KeyGen()

    # Generate evalmult key part for A
    evalMultKey = cc.KeySwitchGen(kp1.secretKey, kp1.secretKey)

    # Generate evalsum key part for A
    cc.EvalSumKeyGen(kp1.secretKey)
    evalSumKeys = cc.GetEvalSumKeyMap(kp1.secretKey.GetKeyTag())

    print("Round 1 of key generation completed.")

    # Round 2 (party B)

    print("Round 2 (party B) started.")

    print("Joint public key for (s_a + s_b) is generated...")
    kp2 = cc.MultipartyKeyGen(kp1.publicKey)

    evalMultKey2 = cc.MultiKeySwitchGen(kp2.secretKey, kp2.secretKey, evalMultKey)

    print("Joint evaluation multiplication key for (s_a + s_b) is generated...")
    evalMultAB = cc.MultiAddEvalKeys(evalMultKey, evalMultKey2, kp2.publicKey.GetKeyTag())

    print("Joint evaluation multiplication key (s_a + s_b) is transformed into s_b*(s_a + s_b)...")
    evalMultBAB = cc.MultiMultEvalKey(kp2.secretKey, evalMultAB, kp2.publicKey.GetKeyTag())

    evalSumKeysB = cc.MultiEvalSumKeyGen(kp2.secretKey, evalSumKeys, kp2.publicKey.GetKeyTag())

    print("Joint evaluation summation key for (s_a + s_b) is generated...")
    evalSumKeysJoin = cc.MultiAddEvalSumKeys(evalSumKeys, evalSumKeysB, kp2.publicKey.GetKeyTag())

    cc.InsertEvalSumKey(evalSumKeysJoin)

    print("Round 2 of key generation completed.")

    print("Round 3 (party A) started.")

    print("Joint key (s_a + s_b) is transformed into s_a*(s_a + s_b)...")
    evalMultAAB = cc.MultiMultEvalKey(kp1.secretKey, evalMultAB, kp2.publicKey.GetKeyTag())

    print("Computing the final evaluation multiplication key for (s_a + s_b)*(s_a + s_b)...")
    evalMultFinal = cc.MultiAddEvalMultKeys(evalMultAAB, evalMultBAB, evalMultAB.GetKeyTag())

    cc.InsertEvalMultKey([evalMultFinal])

    print("Round 3 of key generation completed.")

    ############################################################
    ## Encode source data
    ############################################################

    vectorOfInts1 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
    vectorOfInts2 = [1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    vectorOfInts3 = [2.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 0.0, 0.0]

    plaintext1 = cc.MakeCKKSPackedPlaintext(vectorOfInts1)
    plaintext2 = cc.MakeCKKSPackedPlaintext(vectorOfInts2)
    plaintext3 = cc.MakeCKKSPackedPlaintext(vectorOfInts3)

    ############################################################
    ## Encryption
    ############################################################

    ciphertext1 = cc.Encrypt(kp2.publicKey, plaintext1)
    ciphertext2 = cc.Encrypt(kp2.publicKey, plaintext2)
    ciphertext3 = cc.Encrypt(kp2.publicKey, plaintext3)

    ############################################################
    ## EvalAdd Operation on Re-Encrypted Data
    ############################################################

    ciphertextAdd12 = cc.EvalAdd(ciphertext1, ciphertext2)
    ciphertextAdd123 = cc.EvalAdd(ciphertextAdd12, ciphertext3)

    ciphertextMultTemp = cc.EvalMult(ciphertext1, ciphertext3)
    ciphertextMult = cc.ModReduce(ciphertextMultTemp)
    ciphertextEvalSum = cc.EvalSum(ciphertext3, batchSize)

    ############################################################
    ## Decryption after Accumulation Operation on Encrypted Data with Multiparty
    ############################################################

    dec_plaintext = cc.Decrypt(kp2.secretKey, ciphertext1)
    print("Key 5 decryption:", dec_plaintext)

    ciphertextPartial1 = cc.MultipartyDecryptLead([ciphertextAdd123], kp1.secretKey)
    ciphertextPartial2 = cc.MultipartyDecryptMain([ciphertextAdd123], kp2.secretKey)

    partialCiphertextVec = [ciphertextPartial1[0], ciphertextPartial2[0]]

    plaintextMultipartyNew = cc.MultipartyDecryptFusion(partialCiphertextVec)

    print("\n Original Plaintext: \n")
    print(plaintext1)
    print(plaintext2)
    print(plaintext3)

    plaintextMultipartyNew.SetLength(plaintext1.GetLength())

    print("\n Resulting Fused Plaintext: \n")
    print(plaintextMultipartyNew)

    print("\n")

    ciphertextPartial1 = cc.MultipartyDecryptLead([ciphertextMult], kp1.secretKey)
    ciphertextPartial2 = cc.MultipartyDecryptMain([ciphertextMult], kp2.secretKey)

    partialCiphertextVecMult = [ciphertextPartial1[0], ciphertextPartial2[0]]

    plaintextMultipartyMult = cc.MultipartyDecryptFusion(partialCiphertextVecMult)

    plaintextMultipartyMult.SetLength(plaintext1.GetLength())

    print("\n Resulting Fused Plaintext after Multiplication of plaintexts 1 and 3: \n")
    print(plaintextMultipartyMult)

    print("\n")

    ciphertextPartial1 = cc.MultipartyDecryptLead([ciphertextEvalSum], kp1.secretKey)
    ciphertextPartial2 = cc.MultipartyDecryptMain([ciphertextEvalSum], kp2.secretKey)

    partialCiphertextVecEvalSum = [ciphertextPartial1[0], ciphertextPartial2[0]]

    plaintextMultipartyEvalSum = cc.MultipartyDecryptFusion(partialCiphertextVecEvalSum)

    plaintextMultipartyEvalSum.SetLength(plaintext1.GetLength())

    print("\n Fused result after the Summation of ciphertext 3: \n")
    print(plaintextMultipartyEvalSum)

if __name__ == '__main__':
    main()