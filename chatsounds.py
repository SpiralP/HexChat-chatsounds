__module_name__ = 'chatsounds'
__module_author__ = 'SpiralP'
__module_version__ = '1'
__module_description__ = 'chatsounds'

import hexchat
import os

from pybass import *
from vpk2reader import *


CHATSOUNDS_DIR='D:\\music\\'


HEXCHAT_CONFIG_DIR=hexchat.get_info('configdir')
CONFIG_DIR=os.path.join(CONFIG_DIR, 'chatsounds')

CLEAR='\017'
BOLD='\002'
UNDERLINE='\037'
COLOR='\003'
RED=COLOR+'04'
GREEN=COLOR+'03'
BLUE=COLOR+'02'

def success(msg):
	hexchat.prnt(BOLD + GREEN + msg)
def info(msg):
	hexchat.prnt(BOLD + BLUE + msg)
def warn(msg):
	hexchat.prnt(BOLD + RED + msg)





indexes = {}
def getVpk(path):
	if path in indexes:
		return indexes[path]
	
	indexes[path] = VpkIndex(path)
	return indexes[path]


def loadVpks()
	
	
	
	




channels = []
def command_callback(word, word_eol, userdata):
	name = word[1]
	
	
	if name=='sh':
		for chan in channels:
			BASS_ChannelStop(chan)
		
		del channels[:]
	
	
	name = os.path.join(CHATSOUNDS_DIR,name)
	
	chan = BASS_StreamCreateFile(False, name, 0, 0, 0)
	channels.append(chan)
	
	BASS_ChannelPlay(chan, False)
	
	return hexchat.EAT_ALL
hexchat.hook_command('chatsounds',command_callback)




def unload_callback(userdata):
	print('unloading')
	BASS_Free()
hexchat.hook_unload(unload_callback)


if BASS_Init(-1, 44100, 0, 0, 0):
	success("BASS loaded!")
else:
	warn("BASS COULD NOT BE LOADED!")

	

print('%s version %s loaded.' % (__module_name__,__module_version__))


loadVpks()
