__module_name__ = 'chatsounds'
__module_author__ = 'SpiralP'
__module_version__ = '1'
__module_description__ = 'chatsounds'

import os, sys
import urllib2, json
import re

import hexchat


HEXCHAT_CONFIG_DIR=hexchat.get_info('configdir')
HEXCHAT_ADDONS_DIR=os.path.join(HEXCHAT_CONFIG_DIR,'addons')

CONFIG_DIR=os.path.join(HEXCHAT_CONFIG_DIR, 'chatsounds')
LISTS_DIR=os.path.join(CONFIG_DIR,'lists')

if not os.path.exists(LISTS_DIR):
	os.makedirs(LISTS_DIR)


if CONFIG_DIR not in sys.path:
	sys.path.insert(0, CONFIG_DIR) # for imports

os.environ['PATH'] = os.environ['PATH'] + ';' + CONFIG_DIR # for dlls


PYBASS_DOWNLOAD_URL='http://sourceforge.net/projects/pybass/files/latest/download?source=files'
BASS_DOWNLOAD_URL='http://www.un4seen.com/files/bass24.zip'
VPKREADER_URL='https://raw.githubusercontent.com/SpiralP/HexChat-chatsounds/master/vpk2reader.py'

CHATSOUNDS_DIR='D:\\music\\'
CHATSOUNDS_REPO='https://api.github.com/repos/Metastruct/garrysmod-chatsounds/contents/lua/chatsounds/'


LIST_REGEX='L\["(.+)"\]={{path="(.+)",length=(.+)}}'


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

def _exists(name):
	return name in globals()

def merge(a,b):
	c = a.copy()
	c.update(b)
	return c



try:
	from pybass import *
except ImportError:
	warn('pybass could not be imported, try running ' + BLUE + '/chatsounds setup')
except WindowsError, e:
	warn('bass.dll could not be loaded ({})'.format(e))

try:
	from vpk2reader import *
except ImportError:
	warn('vpk2reader could not be imported, try running ' + BLUE + '/chatsounds setup')



class http():
	def __init__(self, url):
		self.web = urllib2.urlopen(url)
	
	def __enter__(self):
		return self.web
	def __exit__(self, type, value, traceback):
		self.web.close()
	
	def __str__(self):
		return str(self.web)
	

def getLists(path=None):
	links = {}
	with http('{}{}'.format(CHATSOUNDS_REPO,path)) as web:
		data = json.load(web)

	for a in data:
		link = "{}/{}".format(path,a['name'])
		hash = a['sha']
		if a['type']=='file':
			links[hash] = a['download_url']
		elif a['type']=='dir':
			links = merge(getLists(link),links)
	
	return links


def setupPybass():
	def msg(a):
		hexchat.prnt('['+GREEN+'pybass'+CLEAR+'] ' + BLUE + a)
	
	from zipfile import ZipFile
	
	archive_path = os.path.join(CONFIG_DIR,'pybass.zip')
	
	msg('downloading')
	with http(PYBASS_DOWNLOAD_URL) as web:
		with open(archive_path,'wb') as file:
			file.write(web.read())
	
	msg('extracting')
	with ZipFile(archive_path) as zip:
		zip.extractall(CONFIG_DIR)
	
	msg('cleaning up')
	os.remove(archive_path)
	
	with open(os.path.join(CONFIG_DIR,'pybass','__init__.py'),'wb') as file:
		file.write('from pybass import *\n') # compat
	
def setupBass():
	def msg(a):
		hexchat.prnt('['+GREEN+'bass'+CLEAR+'] ' + BLUE + a)
	
	from zipfile import ZipFile
	
	import platform
	if platform.system()=='Darwin': # OSX
		x64 = sys.maxsize > 2**32
	else: # all others
		x64 = platform.architecture()[0]=='64bit'
	
	msg("Looks like you {} using a 64 bit python!".format(UNDERLINE+(x64 and 'are' or 'are NOT')+CLEAR+BLUE))
	
	
	archive_path = os.path.join(CONFIG_DIR,'bass.zip')
	
	msg('downloading bass')
	with http(BASS_DOWNLOAD_URL) as web:
		with open(archive_path,'wb') as file:
			file.write(web.read())
	
	
	
	msg('extracting')
	with ZipFile(archive_path) as zip:
		zip.extractall(os.path.join(CONFIG_DIR,'bass'),[x64 and 'x64/bass.dll' or 'bass.dll'])
	
	dll_path=x64 and os.path.join(CONFIG_DIR,'bass','x64','bass.dll') or os.path.join(CONFIG_DIR,'bass','bass.dll')
	
	msg('moving bass.dll')
	os.rename(dll_path,os.path.join(CONFIG_DIR,'bass.dll'))
	
	
	msg('cleaning up')
	os.remove(archive_path)
	
	if x64:
		os.rmdir(os.path.join(CONFIG_DIR,'bass','x64'))
	os.rmdir(os.path.join(CONFIG_DIR,'bass'))



indexes = {}
def getVpk(path):
	if path in indexes:
		return indexes[path]
	
	indexes[path] = VpkIndex(path)
	return indexes[path]


def loadVpks():
	return



channels = []
def command_callback(word, word_eol, userdata):
	name = word[1]
	
	
	if name=='sh':
		for chan in channels:
			BASS_ChannelStop(chan)
		del channels[:]
		return hexchat.EAT_ALL
	elif name=='setup':
		
		setupPybass()
		setupBass()
		
		with http(VPKREADER_URL) as web:
			with open(os.path.join(CONFIG_DIR,'vpk2reader.py'),'wb') as file:
				file.write(web.read())
		
		success("Setup complete! Reload the plugin: "+BLUE+"/reload chatsounds.py")
		
		
		return hexchat.EAT_ALL
	elif name=='downloadlists':
		
		info('Finding lists')
		lists = merge(getLists('lists_nosend'),getLists('lists_send'))
		
		deleted=0
		uptodate=0
		updated=0
		
		for filename in os.listdir(LISTS_DIR):
			if filename not in lists:
				os.remove(os.path.join(LISTS_DIR,filename))
				deleted+=1
		
		info('Downloading lists')
		for hash,url in lists.iteritems():
			filename = os.path.join(LISTS_DIR,hash)
			if os.path.exists(filename):
				uptodate+=1
				continue
			
			with http(url) as web:
				data = web.read()
			
			items = re.findall(LIST_REGEX,data)
			
			with open(filename,'wb') as file:
				for name,path,length in items:
					file.write(
						'\t'.join((name,path,length))
					)
					file.write('\n')
				file.close()
			
			updated+=1
		
		
		info('{} uptodate'.format(uptodate))
		warn('{} deleted'.format(deleted))
		success('{} updated'.format(updated))
		
		
		loadLists()
		
		return hexchat.EAT_ALL
		
		
	
	
	name = os.path.join(CHATSOUNDS_DIR,name)
	
	"""
	
	get path from lists
	check chatsounds if ^chatsounds/...
		chan = BASS_StreamCreateFile(False, path, 0, 0, 0)
	else vpks
		data = f.getData()
		chan = BASS_StreamCreateFile(True, data, 0, len(data), 0)
	
	"""
	
	
	if not os.path.exists(name):
		# check vpks
		return hexchat.EAT_ALL
	
	
	channels.append(chan)
	
	BASS_ChannelPlay(chan, False)
	
	return hexchat.EAT_ALL
hexchat.hook_command('chatsounds',command_callback)




def unload_callback(userdata):
	info('Unloading {}'.format(__module_name__))
	if _exists('BASS_Free'):
		BASS_Free()
	else:
		warn("BASS doesn't exist to unload!")
	
hexchat.hook_unload(unload_callback)

if _exists('BASS_Init'):
	if BASS_Init(-1, 44100, 0, 0, 0):
		success("BASS loaded!")
	else:
		warn("BASS COULD NOT BE LOADED! ({})".format(get_error_description(BASS_ErrorGetCode())))
else:
	warn("BASS COULD NOT BE LOADED! ({})".format("library missing"))


print('%s version %s loaded.' % (__module_name__,__module_version__))

