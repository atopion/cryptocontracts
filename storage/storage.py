from core import core, transmission
from storage import config
import plyvel
import json
import os

db = plyvel.DB(os.getenv('DB_PATH_OVERRIDE', config.get('database', 'path')), create_if_missing=True)

def get_head():
	return db.get('head'.encode('utf-8')).decode('utf-8')
def _set_head(blockId):
	db.put('head'.encode('utf-8'), blockId.encode('utf-8'))

def put_block(block):
	if not isinstance(block, transmission.Transmission):
		raise TypeError('Not a Core.Transmission block object')

	assert block.previous_hash == get_head()

	db.put(block.transmission_hash.encode('utf-8'), block.to_json().encode('utf-8'))
	_set_head(block.transmission_hash)
	
def get_block(blockId):
	block = db.get(blockId.encode('utf-8'))
	if block is None:
		raise KeyError('blockId does not exist: ' + blockId)
	return transmission.Transmission.from_json(block.decode('utf-8'))

def block_exists(blockId):
	return db.get(blockId.encode('utf-8')) is not None


def get_subchain(targetBlockId):
	target = get_block(targetBlockId)
	if target is None:
		raise KeyError('Block does not exist: ' + targetBlockId)

	curBlock = get_block(get_head())
	chain = []
	while curBlock.transmission_hash != targetBlockId:
		chain.append(curBlock)
		curBlock = get_block(curBlock.previous_hash)
	
	chain.append(target)
	return chain

def print_chain(chain):
	print('[%s]' % ','.join([block.to_json() for block in chain]) )
def print_all():
	print('[%s]' % ','.join([value.decode('utf-8') for key,value in db if key.decode('utf-8') != 'head']) )


# init empty db with root block
if db.get('head'.encode('utf-8')) is None:
	_set_head('ROOT')
	put_block(core.produce_transmission_dummy('ROOT', ['ROOT_KEY_1', 'ROOT_KEY_2'], 'ROOT_DOCUMENT_HASH', 'ROOT_SIGNED_DOCUMENT_HASH', 'ROOT_TRANSMISSION_HASH'))

