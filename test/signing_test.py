#needs 3 key pairs created with 'generate-test-files.sh'

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random
from base64 import b64encode, b64decode
import math

MAX_ENCRYPT_LENGTH = 214
TEST_MESSAGE = "This is a test message to test things"

class Signing(object):

	def sign(self, value, keys):
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

	
	def unsign(self, value, keys):
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

	#Tests all of Signing's functions
	def test(self):
		file1_1 = open("./generated-files/key-1", 'r')
		file1_2 = open("./generated-files/key-1", 'r')
		file1_3 = open("./generated-files/key-1", 'r')
		key1pub = [file1_1.read(), file1_2.read(), file1_3.read()]
		file2_2 = open("./generated-files/key-1.pub", 'r') 
		file2_1 = open("./generated-files/key-1.pub", 'r') 
		file2_3 = open("./generated-files/key-1.pub", 'r')
		key1 = [RSA.import_key(file2_1.read(), None).export_key("PEM").decode('utf-8'),RSA.import_key(file2_2.read(), None).export_key("PEM").decode('utf-8'),RSA.import_key(file2_3.read(), None).export_key("PEM").decode('utf-8')]	
		print("Length before encryption: ", len(bytes(TEST_MESSAGE, 'utf-8')), "\n")
		print ("Message: ", TEST_MESSAGE, "\n")
		signed_key = Signing().sign(TEST_MESSAGE, key1)
		print("Encoded Message:")
		print(signed_key, "\n")
		print("Decoded Message:")
		print(Signing().unsign(signed_key, key1pub))

if __name__ == "__main__":
	Signing().test()
