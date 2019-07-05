from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random
from base64 import b64encode, b64decode

class Signing(object):
	#Signs 'hash' with 'private_key'
	def sign(sign, hash, private_key):
		return PKCS1_OAEP.new(RSA.import_key(private_key)).encrypt(hash)

	#Unsings 'hash' with 'public_key'
	def unsign(self, hash, public_key):
		return PKCS1_OAEP.new(RSA.import_key(public_key)).decrypt(hash)

	#returns new, random key as tuple of strings
	def new_key(self):
		random_generator = Random.new().read
		key = RSA.generate(2048, random_generator)
		#private, public = key, key.publickey()
		return (key.export_key("PEM"), key.publickey().export_key("PEM"))

	#Writes 'key' to 'directory', encrypted with 'password'
	def write_key(self, key, directory, password):
		encrypted_key = RSA.import_key(key).export_key(passphrase=password, pkcs=8, protection="scryptAndAES128-CBC")
		file = open(directory, 'wb')
		file.write(encrypted_key)

	#Reads a key from 'directory', decrypted with 'password'
	def read_key(self, directory, password):
		file = open(directory, 'r')
		return RSA.import_key(file.read(), password).export_key("PEM")

	#Tests all of Signing's functions
	#def test(self):
	#	(key1, key1pub)  = Signing().new_key()
	#	print(key1pub)
	#	print(key1)
	#	signed_key = b64encode(Signing().sign("Test Message", key1))
	#	print("Encoded Message:")
	#	print(signed_key)
	#	print("Decoded Message:")
	#	print(Signing().unsign(b64decode(signed_key), key1))
	#	Signing().write_key(key1, "rsa_test_dir.bin", "hallo")
	#	print(Signing().read_key("rsa_test_dir.bin", "hallo"))

#if __name__ == "__main__":
#	Signing().test()
