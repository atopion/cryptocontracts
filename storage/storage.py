import plyvel
import json

#from storage.block import Block
from core.core import Transmission
from storage import config

db = plyvel.DB(config.get('database', 'path'), create_if_missing=True)


def get_head():
	return db.get('head'.encode('utf-8')).decode('utf-8')
def _set_head(blockId):
	db.put('head'.encode('utf-8'), blockId.encode('utf-8'))


def put_block(block):
	if not isinstance(block, Transmission):
		raise TypeError('Not a Core.Transmission block object')

	assert block.previous_hash == get_head()

	db.put(block.transmission_hash.encode('utf-8'), block.to_json().encode('utf-8'))
	_set_head(block.transmission_hash)
	
def get_block(blockId):
	return Transmission.from_json(db.get(blockId.encode('utf-8')).decode('utf-8'))

def get_subchain(targetBlockId):
	target = get_block(targetBlockId)
	if target is None:
		raise KeyError('Block does not exist: ' + startBlockId)

	curBlock = get_block(get_head())
	chain = []
	while curBlock.transmission_hash != targetBlockId:
		chain.append(curBlock)
		curBlock = get_block(curBlock.previous_hash)
	
	chain.append(target)
	return chain

def init_chain():
	#TODO put proper root block
	_set_head('ROOT')

def print_chain(chain):
	print('[%s]' % ','.join([block.to_json() for block in chain]) )
def print_all():
	print('[%s]' % ','.join([value.decode('utf-8') for key,value in db if key.decode('utf-8') != 'head']) )

