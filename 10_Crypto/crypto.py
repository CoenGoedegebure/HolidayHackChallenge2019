import datetime
from Crypto.Cipher import DES

encrypted_doc = "ElfUResearchLabsSuperSledOMaticQuickStartGuideV1.2.pdf.enc"
output_doc = "ElfUResearchLabsSuperSledOMaticQuickStartGuideV1.2.pdf"


# Generate the secret key given the seed and the key length
def generate_key(key_seed, key_len):
    tmp_key = ""
    for i in range(0, key_len):
        key_seed = ((214013 * key_seed + 2531011) & 0x7fffffff)
        tmp_key = f'{tmp_key}{(key_seed >> 16) & 0x0ff:02x}'

    return tmp_key


def decrypt(code, secret_key):
    # Create a new DES instance for the secret key
    des = DES.new(bytes.fromhex(secret_key),
                  DES.MODE_CBC,
                  iv=bytes.fromhex('0000000000000000'))

    # decrypt the document
    return des.decrypt(code)


# We know that it was encrypted on December 6, 2019, between 19:00 and 21:00 UTC.
timezone = datetime.timezone.utc
start_time = round(datetime.datetime(2019, 12, 6, 19, 0, 0, tzinfo=timezone).timestamp())
end_time = round(datetime.datetime(2019, 12, 6, 21, 0, 0, tzinfo=timezone).timestamp())

key_length = 8

# Validating whether the decrypted document is a PDF, we only need the first 4 bytes.
# Because we use a block cipher and the key length, we only need to decrypt the
# first 8 bytes to see whether the key is correct. This saves us a lot of time
with open(encrypted_doc, "rb") as in_file:
    cipher_text = bytearray(in_file.read())[:key_length]

for seed in range(start_time, end_time):
    # Generate a new key for the seed
    key = generate_key(seed, key_length)

    # Decrypt the cipher text
    result = decrypt(cipher_text, key)

    if result[:4] == b'%PDF':
        print(f'Found key: {seed}, key: {key} - {result[:4]}')
        # Knowing the secret key, decrypt the entire file
        with open(encrypted_doc, "rb") as in_file:
            cipher_text = bytearray(in_file.read())
            result = decrypt(cipher_text, key)

            with open(output_doc, 'wb') as out_file:
                out_file.write(result)

        exit(0)
    else:
        print(f'      key: {seed}, key: {key} - {result[:4]}')

# Found key: 1575663650, key: b5ad6a321240fbec - b'%PDF'
