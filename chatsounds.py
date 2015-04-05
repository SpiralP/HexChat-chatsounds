__module_name__ = 'chatsounds'
__module_author__ = 'SpiralP'
__module_version__ = '1'
__module_description__ = 'chatsounds'

import hexchat
import os

from pybass import *


CHATSOUNDS_DIR='D:\\music\\'


def command_callback(word, word_eol, userdata):
	name = word[1]
	
	
	name = os.path.join(CHATSOUNDS_DIR,name)
	
	chan = BASS_StreamCreateFile(False, name, 0, 0, 0)
	
	BASS_ChannelPlay(chan, False)
	
	return hexchat.EAT_ALL
hexchat.hook_command('chatsounds',command_callback)




def unload_callback(userdata):
	print('unloading')
	BASS_Free()
	
	
hexchat.hook_unload(unload_callback)


if not BASS_Init(-1, 44100, 0, 0, 0):
	print("COULD NOT INIT BASS!!!")
	

print('%s version %s loaded.' % (__module_name__,__module_version__))
