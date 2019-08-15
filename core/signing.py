from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random
from base64 import b64encode, b64decode
import math

OWN_PUBLIC_KEY = "OWN PUBLIC KEY"
OWN_PRIVATE_KEY = "OWN PRIVATE KEY"
MAX_ENCRYPT_LENGTH = 214

#Signs 'hash' with private key
def sign(value, keys):
	if isinstance(keys, str):
		keys = [keys]
	signed_value = value.encode('utf-8')
	for key in keys:
		cipher = PKCS1_OAEP.new(RSA.import_key(key))
		if len(signed_value)<MAX_ENCRYPT_LENGTH:
			signed_value = cipher.encrypt(signed_value)
		else:
			signed_value_parts = bytes('', 'utf-8')
			overlap_bytes = 128 % len(signed_value)
			for x in range(math.ceil(len(signed_value)/128)):
				if (overlap_bytes != 0 and x == math.ceil(len(signed_value)/128)-1):
					signed_value_parts = signed_value_parts + cipher.encrypt(signed_value[x*128:x*128+overlap_bytes])
				else:
					signed_value_parts = signed_value_parts + cipher.encrypt(signed_value[x*128:(x+1)*128])
			signed_value = signed_value_parts
	return b64encode(signed_value)

#Unsigns 'hash' with public key
def unsign(value, keys):
	if isinstance(keys, str):
		keys = [keys]
	unsigned_value = b64decode(value)
	for key in keys:
		cipher = PKCS1_OAEP.new(RSA.import_key(key))
		if len(unsigned_value) <= 256:
			unsigned_value = cipher.decrypt(unsigned_value)
		else:
			unsigned_value_parts = bytes('', 'utf-8')
			for x in range(math.ceil(len(unsigned_value)/256)):
				unsigned_value_parts = unsigned_value_parts + cipher.decrypt(unsigned_value[x*256:(x+1)*256])
			unsigned_value = unsigned_value_parts
	return unsigned_value.decode('utf-8')
