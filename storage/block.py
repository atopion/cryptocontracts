from datetime import datetime
import json

class Block:
	def __init__(self, blockId, publicKeys, documentHash, documentHashSigned, prevBlockId, prevBlockIdSigned, timestamp = datetime.utcnow().isoformat()):
		#TODO attr validation
		self.blockId            = blockId
		self.publicKeys         = publicKeys
		self.timestamp          = timestamp
		self.documentHash       = documentHash
		self.documentHashSigned = documentHashSigned
		self.prevBlockId        = prevBlockId
		self.prevBlockIdSigned  = prevBlockIdSigned

	def json(self):
		return json.dumps(self, default=lambda b: b.__dict__)
