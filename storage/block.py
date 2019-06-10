from datetime import datetime
import json

class Block:
	def __init__(self, blockId, keys, documentHash, documentHashSigned, prevBlockId, prevBlockIdSigned, timestamp = datetime.utcnow().isoformat()):
		#TODO attr validation
		self.blockId            = blockId
		self.keys               = keys
		self.timestamp          = timestamp
		self.documentHash       = documentHash
		self.documentHashSigned = documentHashSigned
		self.prevBlockId        = prevBlockId
		self.prevBlockIdSigned  = prevBlockIdSigned

	def json(self):
		return json.dumps(self, default=lambda b: b.__dict__)
