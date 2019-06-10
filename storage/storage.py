import plyvel
import json

from storage.block import Block
from storage import config

db = plyvel.DB(config.get('database', 'path'), create_if_missing=True)


def get_head():
	return db.get('head'.encode('utf-8')).decode('utf-8')
def set_head(blockId):
	db.put('head'.encode('utf-8'), blockId.encode('utf-8'))


def put_block(block):
	if not isinstance(block, Block):
		raise TypeError('Not a Block object')

	assert block.prevBlockId == get_head()

	db.put(block.blockId.encode('utf-8'), block.json().encode('utf-8'))
	set_head(block.blockId)
	
def get_block(blockId):
	jb = json.loads(db.get(blockId.encode('utf-8')).decode('utf-8'))
	b = Block(**jb)
	return b

def get_subchain(targetBlockId):
	target = get_block(targetBlockId)
	if target is None:
		raise KeyError('Block does not exist: ' + startBlockId)

	curBlock = get_block(get_head())
	chain = []
	while curBlock.blockId != targetBlockId:
		chain.append(curBlock)
		curBlock = get_block(curBlock.prevBlockId)
	
	chain.append(target)
	return chain

def init_chain():
	#TODO put proper root block
	set_head('ROOT')


def print_all():
	for key, value in db:
		print('%s: %s'%(key.decode('utf-8'),value.decode('utf-8')))


